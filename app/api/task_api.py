"""
Task API Endpoints
Handles CRUD operations for tasks

SEC-002: SQL Injection vulnerabilities
SEC-004: Broken authorization (IDOR)
SEC-009: XSS vulnerabilities
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import logging

logger = logging.getLogger("taskforce_pro.task_api")

router = APIRouter()


@router.get("/search")
async def search_tasks(
    query: str = Query(..., description="Search query"),
    user_id: Optional[int] = None
):
    """
    Search tasks by title or description.
    
    SEC-002: CRITICAL SQL INJECTION VULNERABILITY
    User input is directly concatenated into SQL query!
    
    Attack examples:
    - query=' OR '1'='1
    - query='; DROP TABLE tasks; --
    - query=' UNION SELECT * FROM users WHERE '1'='1
    """
    from app.core.database import get_db_connection
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # CRITICAL VULNERABILITY: String concatenation in SQL
        # This allows SQL injection attacks!
        sql = f"""
            SELECT id, title, description, assigned_to, status, priority
            FROM tasks
            WHERE title LIKE '%{query}%' OR description LIKE '%{query}%'
        """
        
        # SEC-011: Logging SQL queries with user input
        logger.debug(f"Executing SQL: {sql}")
        
        cursor.execute(sql)  # SQL INJECTION POINT!
        results = cursor.fetchall()
        
        # BUG-002: Connection not closed (memory leak)
        # cursor.close()
        # conn.close()
        
        tasks = []
        for row in results:
            tasks.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],  # SEC-009: No XSS sanitization
                "assigned_to": row[3],
                "status": row[4],
                "priority": row[5]
            })
        
        return {"tasks": tasks, "count": len(tasks)}
        
    except Exception as e:
        # SEC-019: Exposing database errors to users
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}")
async def get_task(task_id: int, current_user_id: int = 1):
    """
    Get a specific task by ID.
    
    SEC-004: INSECURE DIRECT OBJECT REFERENCE (IDOR)
    No authorization check - any user can access any task!
    """
    from app.core.database import get_db_connection
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # SEC-004: No ownership or permission check!
        # User can access tasks that don't belong to them
        sql = f"SELECT * FROM tasks WHERE id = {task_id}"
        
        cursor.execute(sql)  # Also vulnerable to SQL injection!
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Return task without checking if current_user_id has permission
        task = {
            "id": row[0],
            "title": row[1],
            "description": row[2],  # SEC-009: XSS if displayed in web UI
            "assigned_to": row[3],
            "created_by": row[4],
            "status": row[5],
            "priority": row[6],
            "due_date": row[7]
        }
        
        # SEC-020: No audit logging of data access
        # Should log who accessed what task
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_task(
    title: str,
    description: str,
    assigned_to: int,
    current_user_id: int = 1
):
    """
    Create a new task.
    
    SEC-002: SQL Injection in INSERT statement
    SEC-009: XSS vulnerability (no HTML sanitization)
    """
    from app.core.database import get_db_connection
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # SEC-002: SQL Injection via string concatenation
        # SEC-009: No XSS sanitization on title/description
        sql = f"""
            INSERT INTO tasks (title, description, assigned_to, created_by, status, priority)
            VALUES ('{title}', '{description}', {assigned_to}, {current_user_id}, 'open', 'medium')
        """
        
        logger.debug(f"Creating task with SQL: {sql}")
        
        cursor.execute(sql)  # SQL INJECTION POINT!
        conn.commit()
        
        task_id = cursor.lastrowid
        
        # BUG-002: Connection not properly closed
        
        return {
            "id": task_id,
            "title": title,
            "description": description,
            "message": "Task created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{task_id}")
async def update_task(
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    current_user_id: int = 1
):
    """
    Update an existing task.
    
    SEC-004: No authorization check (IDOR)
    SEC-002: SQL Injection vulnerability
    """
    from app.core.database import get_db_connection
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # SEC-004: No check if current_user_id owns or has permission to modify this task!
        
        # Build UPDATE query (vulnerable to SQL injection)
        updates = []
        if title:
            updates.append(f"title = '{title}'")  # SQL INJECTION!
        if description:
            updates.append(f"description = '{description}'")  # SQL INJECTION!
        if status:
            updates.append(f"status = '{status}'")  # SQL INJECTION!
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        sql = f"UPDATE tasks SET {', '.join(updates)} WHERE id = {task_id}"
        
        logger.debug(f"Updating task with SQL: {sql}")
        
        cursor.execute(sql)
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {"message": "Task updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{task_id}")
async def delete_task(task_id: int, current_user_id: int = 1):
    """
    Delete a task.
    
    SEC-004: No authorization check - anyone can delete any task!
    """
    from app.core.database import get_db_connection
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # SEC-004: No permission check!
        # Any user can delete any task they know the ID of
        
        sql = f"DELETE FROM tasks WHERE id = {task_id}"  # Also SQL injection!
        
        cursor.execute(sql)
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # SEC-020: No audit log of deletion
        # Critical action not logged!
        
        return {"message": "Task deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/comments")
async def get_task_comments(task_id: int):
    """
    Get comments for a task.
    
    BUG-004: N+1 query problem
    Each comment fetches user data separately
    """
    from app.core.database import get_db_connection
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get comments
        cursor.execute(f"SELECT id, user_id, comment, created_at FROM comments WHERE task_id = {task_id}")
        comment_rows = cursor.fetchall()
        
        comments = []
        for row in comment_rows:
            comment_id, user_id, comment_text, created_at = row
            
            # BUG-004: N+1 query - fetching user for each comment individually
            cursor.execute(f"SELECT first_name, last_name FROM users WHERE id = {user_id}")
            user_row = cursor.fetchone()
            
            comments.append({
                "id": comment_id,
                "comment": comment_text,  # SEC-009: No XSS sanitization
                "user": {
                    "first_name": user_row[0] if user_row else "Unknown",
                    "last_name": user_row[1] if user_row else "User"
                },
                "created_at": created_at
            })
        
        return {"comments": comments}
        
    except Exception as e:
        logger.error(f"Error fetching comments: {e}")
        raise HTTPException(status_code=500, detail=str(e))
