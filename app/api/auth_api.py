"""
Authentication API Endpoints
Handles login, registration, and user profile operations.

Intentional vulnerabilities (workshop targets):
  SEC-002 — SQL injection in login & register
  SEC-004 — IDOR on /users/{id}  (no ownership check)
  SEC-011 — Credentials logged in plaintext
  SEC-012 — No rate limiting on login (brute-force allowed)
  SEC-013 — Passwords stored & compared in plaintext
  SEC-019 — User profile exposes password field
"""

from fastapi import APIRouter, HTTPException
import logging

logger = logging.getLogger("taskforce_pro.auth_api")

router = APIRouter()


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------

@router.post("/login")
async def login(email: str, password: str):
    """
    Authenticate a user and return a JWT token.

    SEC-002: SQL injection via string concatenation.
    SEC-011: Credentials logged in plaintext.
    SEC-012: No rate limiting — unlimited brute-force attempts allowed.
    SEC-013: Password compared in plaintext (no hashing).

    Try this in the workshop:
        POST /api/v1/auth/login?email=admin%40globaltech.com%27+OR+%271%27%3D%271&password=x
    """
    from app.core.database import get_db_connection
    from app.auth.jwt_handler import JWTHandler

    # SEC-011: Logging credentials in plaintext!
    logger.debug(f"Login attempt — email: {email}  password: {password}")

    conn = get_db_connection()
    cur = conn.cursor()

    # SEC-002: String-concatenated SQL — vulnerable to injection
    # e.g. email = "admin@globaltech.com' --" bypasses password check
    sql = (
        f"SELECT * FROM users "
        f"WHERE email = '{email}' AND password = '{password}'"
    )
    logger.debug(f"Executing: {sql}")  # SEC-011: SQL with credentials in logs

    cur.execute(sql)  # ← SQL INJECTION
    user = cur.fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # SEC-011: Including plaintext password in JWT payload
    token_data = {
        "user_id": user["id"],
        "email":   user["email"],
        "role":    user["role"],
        "password": password,   # ← NEVER put credentials in a token
    }
    token = JWTHandler.create_access_token(token_data)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user["id"],
        "email":   user["email"],
        "role":    user["role"],
    }


# ---------------------------------------------------------------------------
# POST /register
# ---------------------------------------------------------------------------

@router.post("/register")
async def register(email: str, password: str, first_name: str, last_name: str):
    """
    Register a new user account.

    SEC-002: SQL injection in duplicate-check and INSERT.
    SEC-013: Password stored in plaintext (no hashing).
    SEC-013: No password-strength policy enforced.
    """
    from app.core.database import get_db_connection

    # SEC-013: No password validation — "a" is a valid password
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")

    conn = get_db_connection()
    cur = conn.cursor()

    # SEC-002: SQL injection in existence check
    check_sql = f"SELECT id FROM users WHERE email = '{email}'"
    cur.execute(check_sql)
    if cur.fetchone():
        raise HTTPException(status_code=400, detail="Email already registered")

    # SEC-002: SQL injection in INSERT
    # SEC-013: Password stored as plaintext
    insert_sql = (
        f"INSERT INTO users (email, password, first_name, last_name, role) "
        f"VALUES ('{email}', '{password}', '{first_name}', '{last_name}', 'member')"
    )
    cur.execute(insert_sql)  # ← SQL INJECTION
    conn.commit()

    return {
        "user_id": cur.lastrowid,
        "email": email,
        "message": "Registration successful",
    }


# ---------------------------------------------------------------------------
# GET /users/{user_id}
# ---------------------------------------------------------------------------

@router.get("/users/{user_id}")
async def get_user_profile(user_id: int):
    """
    Retrieve any user's profile by ID.

    SEC-004: No authentication or ownership check — any caller can read
             any user's profile including the admin account.
    SEC-019: Returns the plaintext password field to the caller.
    SEC-002: SQL injection via f-string.

    Workshop demo:
        GET /api/v1/auth/users/1  → returns admin password "admin123"
        GET /api/v1/auth/users/6  → returns attacker account details
    """
    from app.core.database import get_db_connection

    conn = get_db_connection()
    cur = conn.cursor()

    # SEC-002: SQL injection  |  SEC-004: no auth check
    cur.execute(f"SELECT * FROM users WHERE id = {user_id}")
    user = cur.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # SEC-019: Returning password to unauthenticated callers!
    return {
        "id":         user["id"],
        "email":      user["email"],
        "password":   user["password"],   # ← NEVER return this
        "first_name": user["first_name"],
        "last_name":  user["last_name"],
        "role":       user["role"],
        "is_active":  user["is_active"],
    }


# ---------------------------------------------------------------------------
# GET /users  (admin only — but no check is done)
# ---------------------------------------------------------------------------

@router.get("/users")
async def list_all_users():
    """
    List all users including passwords.

    SEC-004: No admin role check — any user (or unauthenticated request) can
             dump the entire user table including plaintext passwords.
    """
    from app.core.database import get_db_connection

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, email, password, first_name, last_name, role FROM users")
    rows = cur.fetchall()

    # SEC-019: Exposing password for all users
    return {
        "users": [dict(r) for r in rows],
        "count": len(rows),
    }
