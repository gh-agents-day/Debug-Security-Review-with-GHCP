"""
In-Memory SQLite Database with Sample Data
TaskForce Pro - Workshop Edition

This module provides a SQLite in-memory database pre-loaded with
realistic sample data so participants can run the app immediately
without any external database setup.
"""

import sqlite3
import threading
import logging

logger = logging.getLogger("taskforce_pro.database")

# Global shared connection - persists for application lifetime
_connection: sqlite3.Connection | None = None
_lock = threading.Lock()


def get_db_connection() -> sqlite3.Connection:
    """
    Get the shared in-memory SQLite connection.

    BUG-002: Single global connection is NOT thread-safe under concurrent load.
    In production, use a proper connection pool (e.g. SQLAlchemy, asyncpg).
    """
    global _connection
    if _connection is None:
        with _lock:
            if _connection is None:
                _connection = sqlite3.connect(":memory:", check_same_thread=False)
                _connection.row_factory = sqlite3.Row
                _connection.execute("PRAGMA journal_mode=WAL")
                _create_schema()
                _seed_data()
                logger.info("In-memory database initialised with sample data")
    return _connection


def init_database():
    """Called at application startup to eagerly initialise the DB."""
    get_db_connection()


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def _create_schema():
    conn = _connection
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT    UNIQUE NOT NULL,
            password    TEXT    NOT NULL,
            first_name  TEXT    NOT NULL,
            last_name   TEXT    NOT NULL,
            role        TEXT    DEFAULT 'member',
            is_active   INTEGER DEFAULT 1,
            is_verified INTEGER DEFAULT 1,
            created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS projects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            description TEXT,
            owner_id    INTEGER NOT NULL,
            status      TEXT    DEFAULT 'active',
            created_at  TEXT    DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            description TEXT,
            assigned_to INTEGER,
            created_by  INTEGER NOT NULL,
            project_id  INTEGER,
            status      TEXT    DEFAULT 'open',
            priority    TEXT    DEFAULT 'medium',
            due_date    TEXT,
            created_at  TEXT    DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assigned_to) REFERENCES users(id),
            FOREIGN KEY (created_by)  REFERENCES users(id),
            FOREIGN KEY (project_id)  REFERENCES projects(id)
        );

        CREATE TABLE IF NOT EXISTS comments (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id    INTEGER NOT NULL,
            user_id    INTEGER NOT NULL,
            comment    TEXT    NOT NULL,
            created_at TEXT    DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id)  REFERENCES tasks(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS attachments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id     INTEGER NOT NULL,
            filename    TEXT    NOT NULL,
            file_path   TEXT    NOT NULL,
            uploaded_by INTEGER NOT NULL,
            created_at  TEXT    DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            action     TEXT    NOT NULL,
            resource   TEXT    NOT NULL,
            detail     TEXT,
            ip_address TEXT,
            created_at TEXT    DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# Seed data  –  realistic Fortune-100 scenario
# ---------------------------------------------------------------------------

def _seed_data():
    conn = _connection
    cur = conn.cursor()

    # ------------------------------------------------------------------
    # Users  (passwords stored in PLAINTEXT — intentional SEC-013 bug)
    # ------------------------------------------------------------------
    users = [
        (1, "admin@globaltech.com",       "admin123",       "System",    "Admin",      "admin"),
        (2, "sarah.chen@globaltech.com",   "Password123",    "Sarah",     "Chen",       "manager"),
        (3, "mike.rodriguez@globaltech.com","Password123",   "Mike",      "Rodriguez",  "developer"),
        (4, "jennifer.park@globaltech.com", "Password123",   "Jennifer",  "Park",       "developer"),
        (5, "david.kim@globaltech.com",    "Password123",    "David",     "Kim",        "member"),
        (6, "attacker@evil.com",           "hacked",         "Evil",      "Attacker",   "member"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO users (id,email,password,first_name,last_name,role) VALUES(?,?,?,?,?,?)",
        users,
    )

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------
    projects = [
        (1, "Q2 Product Launch",       "Critical Q2 product milestones",                2),
        (2, "Security Audit 2026",     "Annual SOC 2 / ISO-27001 compliance tasks",     1),
        (3, "Customer Portal v3",      "Self-service portal redesign",                  3),
        (4, "M&A Integration — ACME",  "CONFIDENTIAL: acquisition integration work",    2),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO projects (id,name,description,owner_id) VALUES(?,?,?,?)",
        projects,
    )

    # ------------------------------------------------------------------
    # Tasks  (include sensitive data to make IDOR demo realistic)
    # ------------------------------------------------------------------
    tasks = [
        (1,  "Implement S3 file uploads",
             "Add attachment feature via AWS S3. Credentials in config/production.yaml.",
             3, 2, 1, "in_progress", "high",     "2026-04-30"),
        (2,  "Fix SQL injection in task-search endpoint",
             "CRITICAL: search query is concatenated directly into SQL. See task_api.py line 30.",
             3, 1, 2, "open",        "critical",  "2026-04-20"),
        (3,  "Rotate JWT secret — exposed in GitHub commit",
             "JWT secret 'super-secret-jwt-key-do-not-share-2026' was pushed publicly.",
             4, 1, 2, "open",        "critical",  "2026-04-18"),
        (4,  "Q1 billing reconciliation — Bank of America",
             "CONFIDENTIAL: Invoice #INV-2026-0412, amount $2,500,000. Contact: j.smith@boa.com",
             4, 2, 1, "open",        "medium",    "2026-04-25"),
        (5,  "Deploy v2.4.1 to production",
             "Deployment runbook: ssh deploy@prod-01.globaltech.internal -i ~/.ssh/prod_rsa",
             3, 2, 1, "completed",   "high",      "2026-04-15"),
        (6,  "SOC 2 evidence collection",
             "SENSITIVE: Audit evidence package for EY. See SharePoint /Compliance/SOC2-2026/",
             1, 1, 2, "in_progress", "high",      "2026-04-30"),
        (7,  "Onboard ACME Corp — $8M deal",
             "CONFIDENTIAL: Legal NDA signed. Primary contact: ceo@acme.com / +1-415-555-0199",
             2, 2, 4, "open",        "high",      "2026-05-01"),
        (8,  "Patch IDOR: users can view each other's tasks",
             "BUG: GET /api/v1/tasks/{id} has no ownership check. Any logged-in user can read any task.",
             3, 1, 2, "open",        "critical",  "2026-04-18"),
    ]
    cur.executemany(
        """INSERT OR IGNORE INTO tasks
           (id,title,description,assigned_to,created_by,project_id,status,priority,due_date)
           VALUES(?,?,?,?,?,?,?,?,?)""",
        tasks,
    )

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------
    comments = [
        (1, 1, 3, "Started S3 integration. Used credentials from config/production.yaml — is that safe?"),
        (2, 2, 1, "Attack proof-of-concept: curl '/api/v1/tasks/search?query=%27+OR+%271%27%3D%271'"),
        (3, 3, 4, "Tokens expire in 30 days. Any stolen token stays valid for a month!"),
        (4, 8, 6, "I can see task #7 even though I'm not assigned. This is the IDOR bug in action."),
        (5, 5, 2, "Prod SSH key path: /home/deploy/.ssh/prod_rsa — REMOVE THIS COMMENT!"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO comments (id,task_id,user_id,comment) VALUES(?,?,?,?)",
        comments,
    )

    conn.commit()
    logger.info("Sample data seeded: 6 users, 4 projects, 8 tasks, 5 comments")
