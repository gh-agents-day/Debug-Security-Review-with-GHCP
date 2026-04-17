"""
Application Settings
Loads configuration from environment variables with hardcoded fallbacks.

SEC-006: Hardcoded fallback values expose production secrets when env vars are missing.
"""

import os
from functools import lru_cache


class Settings:
    """
    Application settings.

    BUG: Using hardcoded defaults means the app "works" even when secrets
    are not configured — silently using insecure values in production.
    """

    # Application
    APP_NAME: str = "TaskForce Pro"
    VERSION: str = "2.4.1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"  # SEC-008: defaults to True

    # Database — falls back to in-memory SQLite for workshop
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///:memory:",  # Workshop default — safe for demo
    )

    # Redis
    REDIS_URL: str = os.getenv(
        "REDIS_URL",
        "redis://:Red1s#Pr0dP@ss2026@localhost:6379/0",  # SEC-006: hardcoded fallback
    )

    # JWT
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "super-secret-jwt-key-do-not-share-2026",  # SEC-003: hardcoded fallback
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200"))

    # AWS
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE")  # SEC-001
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")  # SEC-001
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "taskforce-pro-attachments")

    # Admin (SEC-005)
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@globaltech.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")  # SEC-005: hardcoded


@lru_cache
def get_settings() -> Settings:
    return Settings()
