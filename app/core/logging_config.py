"""
Logging Configuration
SEC-011: Log level defaults to DEBUG in production, exposing sensitive data.
"""

import logging
import sys


def setup_logging():
    """
    Configure application-wide logging.

    SEC-011: DEBUG level logs may contain passwords, tokens, SQL queries.
    """
    log_level = logging.DEBUG  # Should be INFO or WARNING in production

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
