"""
Pytest configuration and test environment setup.

Ensures that the environment has a safe, isolated in-memory SQLite URL configured
before any module imports backend.database.
"""

import os

# Set fallback in-memory test database URL if not already specified
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
