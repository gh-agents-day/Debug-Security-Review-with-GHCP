"""
Attachment API Endpoints
SEC-016: Path traversal vulnerability in filename handling.
SEC-015: No file type validation (allows malicious uploads).
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
import logging
import os

logger = logging.getLogger("taskforce_pro.attachment_api")
router = APIRouter()

UPLOAD_DIR = "/tmp/taskforce_uploads"


@router.post("/upload/{task_id}")
async def upload_attachment(task_id: int, filename: str, file: UploadFile = File(...)):
    """
    Upload a file attachment for a task.

    SEC-016: PATH TRAVERSAL — filename not sanitised.
    Attacker can pass filename='../../etc/passwd' to overwrite system files.
    SEC-015: No MIME type or extension validation.
    SEC-004: No check that caller owns the task.
    """
    from app.core.database import get_db_connection

    # SEC-016: Unsanitised filename allows path traversal
    file_path = os.path.join(UPLOAD_DIR, filename)  # DANGEROUS!
    logger.debug(f"Saving upload to: {file_path}")

    # In workshop mode we just simulate the save (no real disk write)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO attachments (task_id, filename, file_path, uploaded_by) VALUES (?,?,?,?)",
        (task_id, filename, file_path, 1),
    )
    conn.commit()
    return {"message": "File uploaded", "path": file_path, "attachment_id": cur.lastrowid}


@router.get("/task/{task_id}")
async def list_attachments(task_id: int):
    """List attachments for a task. SEC-004: No ownership check."""
    from app.core.database import get_db_connection

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM attachments WHERE task_id = ?", (task_id,))
    return {"attachments": [dict(r) for r in cur.fetchall()]}
