"""
User API Endpoints
SEC-004: All endpoints lack authentication/authorization checks.
"""

from fastapi import APIRouter, HTTPException
import logging

logger = logging.getLogger("taskforce_pro.user_api")
router = APIRouter()


@router.get("/me")
async def get_current_user(token: str = ""):
    """
    Get current user from JWT token.
    SEC-003: Token not properly validated (no signature check here).
    """
    from app.auth.jwt_handler import JWTHandler

    if not token:
        raise HTTPException(status_code=401, detail="Token required")

    payload = JWTHandler.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    from app.core.database import get_db_connection
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT id, email, first_name, last_name, role FROM users WHERE id = {payload.get('user_id', 0)}")
    user = cur.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(user)


@router.get("/")
async def list_users():
    """List users. SEC-004: No admin check — any caller can list all users."""
    from app.core.database import get_db_connection
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, email, first_name, last_name, role, is_active FROM users")
    return {"users": [dict(r) for r in cur.fetchall()]}
