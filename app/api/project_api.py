"""
Project API Endpoints
Basic project management with intentional code-quality bugs.

BUG-004: N+1 query pattern in list_projects
BUG-002: DB connection not closed after each request
"""

from fastapi import APIRouter, HTTPException
import logging

logger = logging.getLogger("taskforce_pro.project_api")
router = APIRouter()


@router.get("/")
async def list_projects():
    """
    List all projects.

    BUG-004: N+1 query — fetches owner for each project in a loop.
    """
    from app.core.database import get_db_connection

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name, description, owner_id, status FROM projects")
    project_rows = cur.fetchall()

    projects = []
    for row in project_rows:
        # BUG-004: Separate query per project to fetch owner name
        cur.execute(f"SELECT first_name, last_name FROM users WHERE id = {row['owner_id']}")
        owner = cur.fetchone()
        projects.append({
            "id":          row["id"],
            "name":        row["name"],
            "description": row["description"],
            "status":      row["status"],
            "owner": {
                "first_name": owner["first_name"] if owner else "Unknown",
                "last_name":  owner["last_name"]  if owner else "",
            },
        })

    return {"projects": projects, "count": len(projects)}


@router.get("/{project_id}")
async def get_project(project_id: int):
    """Get a specific project. SEC-004: No ownership or permission check."""
    from app.core.database import get_db_connection

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM projects WHERE id = {project_id}")
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    return dict(row)


@router.get("/{project_id}/tasks")
async def get_project_tasks(project_id: int):
    """Get all tasks for a project. BUG-004: N+1 queries per task."""
    from app.core.database import get_db_connection

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM tasks WHERE project_id = {project_id}")
    task_rows = cur.fetchall()

    tasks = []
    for t in task_rows:
        # BUG-004: Per-task user lookup
        cur.execute(f"SELECT email FROM users WHERE id = {t['assigned_to']}")
        assignee = cur.fetchone()
        tasks.append({
            **dict(t),
            "assignee_email": assignee["email"] if assignee else None,
        })

    return {"tasks": tasks, "count": len(tasks)}
