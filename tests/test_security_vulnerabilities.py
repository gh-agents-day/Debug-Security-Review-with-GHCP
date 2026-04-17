"""
Security Vulnerability Tests — TaskForce Pro Workshop
======================================================

Most tests in this file FAIL initially. That is intentional.

Each test documents a real vulnerability. Your job is to:
  1. Run the tests — see them fail (RED)
  2. Understand WHY they fail by reading the test docstring
  3. Fix the corresponding source file
  4. Re-run until all tests pass (GREEN)

Run tests:
    pip install pytest httpx
    pytest tests/test_security_vulnerabilities.py -v

Run with coverage:
    pytest tests/ --cov=app --cov-report=term-missing
"""

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# App client
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    from main import app
    return TestClient(app, raise_server_exceptions=False)


# ===========================================================================
# SEC-002 — SQL Injection
# ===========================================================================

class TestSQLInjection:

    def test_search_sql_injection_returns_no_data(self, client):
        """
        FAILS if vulnerable: search returns all rows when injecting ' OR '1'='1
        PASSES when fixed:   parameterised query returns 0 results for the payload.

        Fix target: app/api/task_api.py  search_tasks()
        """
        response = client.get("/api/v1/tasks/search", params={"query": "' OR '1'='1"})
        assert response.status_code == 200
        data = response.json()
        # A secure endpoint returns 0 tasks for this nonsense query
        assert data["count"] == 0, (
            "SQL injection detected! The search returned rows when it should return 0. "
            "Fix: use parameterised queries (cursor.execute(sql, (param,)))."
        )

    def test_login_sql_injection_rejected(self, client):
        """
        FAILS if vulnerable: attacker logs in as admin without knowing the password.
        PASSES when fixed:   returns 401 for the injected payload.

        Attack payload: email = "admin@globaltech.com' --"

        Fix target: app/api/auth_api.py  login()
        """
        response = client.post(
            "/api/v1/auth/login",
            params={"email": "admin@globaltech.com' --", "password": "wrongpassword"},
        )
        assert response.status_code == 401, (
            "SQL injection in login! Attacker authenticated without a valid password. "
            "Fix: use parameterised queries."
        )

    def test_login_or_injection_rejected(self, client):
        """
        FAILS if vulnerable: ' OR '1'='1 payload returns a token for any user.
        PASSES when fixed:   returns 401.
        """
        response = client.post(
            "/api/v1/auth/login",
            params={"email": "' OR '1'='1' --", "password": "x"},
        )
        assert response.status_code == 401, (
            "SQL injection: OR-based bypass succeeded. Fix with parameterised queries."
        )

    def test_task_search_by_legitimate_title(self, client):
        """Sanity check: legitimate search should return results after fix."""
        response = client.get("/api/v1/tasks/search", params={"query": "SQL injection"})
        assert response.status_code == 200
        assert response.json()["count"] >= 1  # task #2 in seed data matches


# ===========================================================================
# SEC-003 — JWT Configuration
# ===========================================================================

class TestJWTSecurity:

    def test_jwt_secret_not_hardcoded(self):
        """
        FAILS if vulnerable: SECRET_KEY equals the known hardcoded value.
        PASSES when fixed:   SECRET_KEY comes from environment and differs.

        Fix target: app/auth/jwt_handler.py  JWTHandler.SECRET_KEY
        """
        import os
        from app.auth.jwt_handler import JWTHandler

        hardcoded = "super-secret-jwt-key-do-not-share-2026"
        assert JWTHandler.SECRET_KEY != hardcoded, (
            f"JWT secret is still hardcoded to '{hardcoded}'. "
            "Fix: load from os.getenv('JWT_SECRET_KEY') and raise ValueError if missing."
        )

    def test_jwt_secret_minimum_length(self):
        """
        PASSES when fixed: secret is at least 32 characters.
        """
        from app.auth.jwt_handler import JWTHandler
        assert len(JWTHandler.SECRET_KEY) >= 32, (
            "JWT secret is too short. Minimum 32 characters required for HS256."
        )

    def test_jwt_token_expires(self):
        """
        FAILS if vulnerable: tokens are created without expiry (verify_exp=False).
        PASSES when fixed:   decode raises ExpiredSignatureError for old tokens.
        """
        import jwt
        from datetime import datetime, timedelta, timezone
        from app.auth.jwt_handler import JWTHandler

        # Create a token that expired 1 hour ago
        expired_payload = {
            "user_id": 1,
            "exp": datetime.now(tz=timezone.utc) - timedelta(hours=1),
        }
        expired_token = jwt.encode(expired_payload, JWTHandler.SECRET_KEY, algorithm="HS256")

        # decode_token should return None (or raise) for expired tokens
        result = JWTHandler.decode_token(expired_token)
        assert result is None, (
            "Expired JWT token was accepted! "
            "Fix: remove options={'verify_exp': False} from jwt.decode() call."
        )

    def test_token_does_not_contain_password(self, client):
        """
        FAILS if vulnerable: the JWT payload contains the user's plaintext password.
        PASSES when fixed:   'password' key is absent from the decoded payload.
        """
        import base64, json

        response = client.post(
            "/api/v1/auth/login",
            params={"email": "mike.rodriguez@globaltech.com", "password": "Password123"},
        )
        if response.status_code != 200:
            pytest.skip("Login failed — fix SEC-002 first")

        token = response.json().get("access_token", "")
        # Decode payload (middle segment) without verifying signature
        try:
            payload_b64 = token.split(".")[1]
            payload_b64 += "=" * (-len(payload_b64) % 4)
            payload = json.loads(base64.b64decode(payload_b64))
        except Exception:
            pytest.skip("Could not decode token")

        assert "password" not in payload, (
            "JWT payload contains 'password' field! "
            "Fix: remove password from token_data in auth_api.py login()."
        )


# ===========================================================================
# SEC-004 — Broken Authorization / IDOR
# ===========================================================================

class TestAuthorization:

    def test_unauthenticated_user_cannot_list_all_users(self, client):
        """
        FAILS if vulnerable: /auth/users returns user list with no auth header.
        PASSES when fixed:   returns 401 Unauthorized.

        Fix target: app/api/auth_api.py  list_all_users()
        """
        response = client.get("/api/v1/auth/users")
        assert response.status_code == 401, (
            "Unauthenticated request returned user list! "
            "Fix: require a valid Bearer token and admin role."
        )

    def test_user_profile_does_not_expose_password(self, client):
        """
        FAILS if vulnerable: GET /auth/users/1 returns 'password' field.
        PASSES when fixed:   'password' is absent from the response.

        Fix target: app/api/auth_api.py  get_user_profile()
        """
        response = client.get("/api/v1/auth/users/1")
        if response.status_code == 401:
            pytest.skip("Endpoint now requires auth — IDOR partially fixed")
        assert response.status_code in (200, 403)
        if response.status_code == 200:
            assert "password" not in response.json(), (
                "User profile exposes plaintext password! "
                "Fix: exclude 'password' from the response dict."
            )

    def test_regular_user_cannot_access_another_users_task(self, client):
        """
        FAILS if vulnerable: user 6 (attacker) can read task 4 (confidential).
        PASSES when fixed:   returns 403 Forbidden.

        Fix target: app/api/task_api.py  get_task()
        """
        # Simulate request as attacker (user_id=6) accessing task owned by user 2
        response = client.get("/api/v1/tasks/4", params={"current_user_id": 6})
        assert response.status_code == 403, (
            "IDOR: Attacker can read confidential task #4 (Bank of America invoice). "
            "Fix: check that current_user_id matches task.created_by or task.assigned_to."
        )

    def test_regular_user_cannot_delete_others_task(self, client):
        """
        FAILS if vulnerable: user 6 can delete task 7 without permission.
        PASSES when fixed:   returns 403 Forbidden.
        """
        response = client.delete("/api/v1/tasks/7", params={"current_user_id": 6})
        assert response.status_code == 403, (
            "IDOR: Attacker can delete task #7 ($8M ACME deal). "
            "Fix: verify ownership before deletion."
        )


# ===========================================================================
# SEC-005 / SEC-013 — Hardcoded Credentials & Plaintext Passwords
# ===========================================================================

class TestCredentials:

    def test_admin_password_not_hardcoded(self):
        """
        FAILS if vulnerable: admin_setup.py still has 'admin123' hardcoded.
        PASSES when fixed:   ADMIN_PASSWORD comes only from env var.
        """
        import app.auth.admin_setup as setup
        hardcoded = "admin123"
        assert not hasattr(setup, "ADMIN_PASSWORD") or setup.ADMIN_PASSWORD != hardcoded, (
            "Admin password 'admin123' is still hardcoded in admin_setup.py. "
            "Fix: use os.getenv('ADMIN_PASSWORD') and raise if missing."
        )

    def test_passwords_not_stored_in_plaintext(self, client):
        """
        FAILS if vulnerable: /auth/users/3 returns password field as 'Password123'.
        PASSES when fixed:   password field is absent or bcrypt-hashed (starts with '$2b$').
        """
        response = client.get("/api/v1/auth/users/3")
        if response.status_code == 401:
            pytest.skip("Endpoint now requires auth — good progress!")
        if response.status_code != 200:
            return
        data = response.json()
        password_field = data.get("password", "")
        assert password_field.startswith("$2b$") or password_field == "", (
            f"Password stored in plaintext: '{password_field}'. "
            "Fix: hash passwords with bcrypt (passlib) before storing."
        )


# ===========================================================================
# SEC-008 / SEC-019 — Information Disclosure
# ===========================================================================

class TestInformationLeakage:

    def test_debug_mode_not_enabled(self, client):
        """
        FAILS if vulnerable: root endpoint returns debug=True.
        PASSES when fixed:   debug field is false or absent.

        Fix target: main.py  DEBUG variable  +  config.py Settings.DEBUG
        """
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data.get("debug") is not True, (
            "DEBUG=True is exposed in the API root response. "
            "Fix: set DEBUG=False in config and remove from root response."
        )

    def test_error_response_hides_stack_trace(self, client):
        """
        FAILS if vulnerable: unhandled errors return 'traceback' in response body.
        PASSES when fixed:   only a generic message is returned.

        Fix target: main.py  global_exception_handler()
        """
        # Trigger an error by requesting a non-existent task that causes an exception
        response = client.get("/api/v1/tasks/99999")
        if response.status_code == 500:
            assert "traceback" not in response.json(), (
                "Full Python stack trace exposed in HTTP response! "
                "Fix: remove traceback.format_exc() from the error handler response."
            )

    def test_database_url_not_in_root_response(self, client):
        """
        FAILS if vulnerable: root endpoint leaks database host details.
        PASSES when fixed:   'database' key is absent from root response.
        """
        response = client.get("/")
        data = response.json()
        assert "database" not in data, (
            "Database connection info exposed in root endpoint. "
            "Fix: remove the 'database' key from the root response dict."
        )


# ===========================================================================
# SEC-014 — CORS Misconfiguration
# ===========================================================================

class TestCORS:

    def test_cors_not_wildcard(self, client):
        """
        FAILS if vulnerable: Access-Control-Allow-Origin is '*'.
        PASSES when fixed:   header contains specific allowed domain(s).
        """
        response = client.options(
            "/api/v1/tasks/",
            headers={"Origin": "https://evil.com", "Access-Control-Request-Method": "GET"},
        )
        origin_header = response.headers.get("access-control-allow-origin", "")
        assert origin_header != "*", (
            "CORS allows all origins (*). "
            "Fix: replace allow_origins=['*'] with your specific domain list."
        )
