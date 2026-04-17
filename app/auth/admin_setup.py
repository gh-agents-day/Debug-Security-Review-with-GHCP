"""
Admin User Setup
Creates default admin user with hardcoded credentials

SEC-005: CRITICAL - Admin password is hardcoded in source code
"""

import logging
from typing import Optional

logger = logging.getLogger("taskforce_pro.admin")


# SEC-005: HARDCODED ADMIN CREDENTIALS
# CRITICAL VULNERABILITY: Admin password in source code!
ADMIN_EMAIL = "admin@globaltech.com"
ADMIN_PASSWORD = "admin123"  # EXPOSED! Never hardcode passwords!
ADMIN_API_KEY = "sk_admin_super_secret_key_2026"  # EXPOSED!


async def create_admin_user() -> bool:
    """
    Create default admin user if it doesn't exist.
    
    SEC-005: Uses hardcoded admin credentials
    SEC-011: Logs credentials in plaintext
    
    Returns:
        True if created, False otherwise
    """
    from app.core.database import get_db_connection

    try:
        # SEC-011: Logging admin credentials
        logger.info(f"Checking for admin user: {ADMIN_EMAIL}")
        logger.debug(f"Using admin password: {ADMIN_PASSWORD}")  # EXPOSED IN LOGS!

        conn = get_db_connection()
        cur = conn.cursor()

        # Check if admin exists (already seeded on startup)
        cur.execute("SELECT id FROM users WHERE email = ?", (ADMIN_EMAIL,))
        existing_admin = cur.fetchone()

        if existing_admin:
            logger.info("Admin user already exists")
            return False

        # Create new admin user with hardcoded password (SEC-013: No hashing!)
        cur.execute(
            "INSERT INTO users (email, password, first_name, last_name, role) VALUES (?,?,?,?,?)",
            (ADMIN_EMAIL, ADMIN_PASSWORD, "System", "Administrator", "admin"),
        )
        conn.commit()
        
        # SEC-011: Logging success with credentials
        logger.info(f"Admin user created successfully")
        logger.info(f"Email: {ADMIN_EMAIL}, Password: {ADMIN_PASSWORD}")  # EXPOSED!
        logger.info(f"Admin API Key: {ADMIN_API_KEY}")  # EXPOSED!
        
        return True
        
    except Exception as e:
        # BUG-003: Exception swallowed without proper logging
        logger.error(f"Failed to create admin user: {e}")
        return False


# More hardcoded credentials for different environments
DEV_ADMIN_CREDS = {
    "email": "dev-admin@globaltech.com",
    "password": "DevAdmin@2026"  # EXPOSED!
}

STAGING_ADMIN_CREDS = {
    "email": "staging-admin@globaltech.com",
    "password": "StagingAdmin@2026"  # EXPOSED!
}

PROD_ADMIN_CREDS = {
    "email": "prod-admin@globaltech.com",
    "password": "ProdAdmin@2026"  # EXPOSED!
}

# Service account credentials (also hardcoded - bad practice!)
SERVICE_ACCOUNTS = {
    "backup_service": {
        "username": "backup_svc",
        "password": "B@ckup$vc2026",  # EXPOSED!
        "permissions": ["read_all", "write_backups"]
    },
    "reporting_service": {
        "username": "report_svc",
        "password": "Rep0rt$vc2026",  # EXPOSED!
        "permissions": ["read_all"]
    },
    "integration_service": {
        "username": "integration_svc",
        "password": "Int3gr@tion2026",  # EXPOSED!
        "permissions": ["read_all", "write_all"]
    }
}
