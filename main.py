"""
TaskForce Pro - Enterprise Task Management Platform
Main Application Entry Point

⚠️  WARNING: This file contains INTENTIONAL SECURITY VULNERABILITIES
    for workshop training purposes. DO NOT deploy to production.

Vulnerabilities in this file:
  SEC-008 — DEBUG=True exposed in API response
  SEC-014 — CORS allows all origins (*)
  SEC-011 — Sensitive config values logged at startup
  SEC-019 — Full stack traces returned to callers on error

Run the app (workshop mode — no external dependencies needed):
    pip install fastapi uvicorn pyjwt
    python main.py

Then open: http://localhost:8000/docs
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from app.api import auth_api, task_api, project_api, user_api, attachment_api
from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.core.database import init_database

# SEC-008: DEBUG MODE ENABLED IN PRODUCTION
# This is a CRITICAL vulnerability - exposes stack traces, internal paths, and sensitive data
DEBUG = True  # TODO: Should be False in production!

app = FastAPI(
    title="TaskForce Pro API",
    description="Enterprise Task Management Platform for Fortune 500 Companies",
    version="2.4.1",
    debug=DEBUG,  # SEC-008: Debug mode exposes sensitive information
    # docs_url=None,  # Should disable in production
    # redoc_url=None,  # Should disable in production
)

# BUG-011: CORS misconfiguration - allows all origins
# This enables Cross-Site Request Forgery (CSRF) attacks
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # SEC-014: Should be specific domains only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
setup_logging()
logger = logging.getLogger("taskforce_pro")

# Initialize database
init_database()

# Include routers
app.include_router(auth_api.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(task_api.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(project_api.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(user_api.router, prefix="/api/v1/users", tags=["users"])
app.include_router(attachment_api.router, prefix="/api/v1/attachments", tags=["attachments"])


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    settings = get_settings()
    
    # SEC-011: SENSITIVE DATA IN LOGS
    # Logging configuration details including database connection strings
    logger.info(f"Starting TaskForce Pro v2.4.1")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database: {settings.DATABASE_URL}")  # Exposes credentials!
    logger.info(f"Redis: {settings.REDIS_URL}")  # Exposes credentials!
    logger.info(f"AWS Region: {settings.AWS_REGION}")
    
    # SEC-005: Initialize admin user with hardcoded password
    from app.auth.admin_setup import create_admin_user
    await create_admin_user()
    
    logger.info("Application started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down TaskForce Pro")
    # BUG-002: Database connections not properly closed
    # Should close database connection pool here


@app.get("/")
async def root():
    """Root endpoint - returns application info."""
    settings = get_settings()
    return {
        "application": "TaskForce Pro",
        "version": "2.4.1",
        "status": "running",
        "environment": settings.ENVIRONMENT,
        # SEC-019: Information leakage - exposing internal details
        "debug": DEBUG,
        "database": settings.DATABASE_URL.split("@")[1] if "@" in settings.DATABASE_URL else "unknown",
        "features": [
            "Task Management",
            "Project Tracking",
            "Team Collaboration",
            "File Attachments",
            "Webhook Integrations",
            "Analytics & Reporting"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.4.1"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler.
    
    SEC-019: INFORMATION LEAKAGE IN ERROR RESPONSES
    Stack traces and internal error details are exposed to clients
    """
    import traceback
    
    # SEC-019: Exposing full stack trace in response
    error_details = {
        "error": str(exc),
        "type": type(exc).__name__,
        "traceback": traceback.format_exc(),  # CRITICAL: Never expose this!
        "request_path": str(request.url),
        "method": request.method,
    }
    
    # SEC-011: Logging sensitive request details
    logger.error(f"Unhandled exception: {exc}", extra=error_details)
    
    if DEBUG:
        # In debug mode, return full error details (DANGEROUS!)
        return JSONResponse(
            status_code=500,
            content=error_details
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )


if __name__ == "__main__":
    # SEC-008: Running with debug and auto-reload in production
    # SEC-017: No TLS/SSL configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # Binding to all interfaces (security risk)
        port=8000,
        reload=True,  # Auto-reload enabled (should be False in production)
        log_level="debug",  # Verbose logging (should be "info" or "warning" in production)
        # ssl_keyfile=None,  # No SSL configured!
        # ssl_certfile=None,
    )
