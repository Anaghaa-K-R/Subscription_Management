"""
Pytest configuration and test environment setup.

Ensures that the environment has a safe, isolated in-memory SQLite URL configured
before any module imports backend.database.
"""

import os
import sys
from pathlib import Path

# Set fallback in-memory test database URL if not already specified
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Unify canonical module references across test suites
import backend.database
import backend.models
import backend.models.user

sys.modules.setdefault("database", backend.database)
sys.modules.setdefault("models", backend.models)
sys.modules.setdefault("models.user", backend.models.user)
