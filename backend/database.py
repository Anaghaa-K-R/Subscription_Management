import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Find .env in backend/ or root
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

backend_env = BASE_DIR / ".env"
root_env = ROOT_DIR / ".env"

if backend_env.exists():
    load_dotenv(dotenv_path=backend_env)
elif root_env.exists():
    load_dotenv(dotenv_path=root_env)
else:
    load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
ACTIVE_DB_MODE = "production"


def _init_engine():
    global ACTIVE_DB_MODE
    configured_url = os.getenv("DATABASE_URL")
    if configured_url:
        try:
            connect_args = {"connect_timeout": 2} if "postgres" in configured_url else {}
            probe_engine = create_engine(configured_url, connect_args=connect_args)
            with probe_engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("SELECT 1"))
            ACTIVE_DB_MODE = "production"
            return probe_engine
        except Exception as e:
            print(f"[DATABASE NOTICE] Configured external database is unreachable: {e}")
            print(f"[DATABASE NOTICE] Operating safely in local demo database mode (subscriptiq_local_demo.db).")

    demo_path = BASE_DIR / "subscriptiq_local_demo.db"
    ACTIVE_DB_MODE = "local_demo"
    return create_engine(f"sqlite:///{demo_path}", connect_args={"check_same_thread": False})


engine = _init_engine()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    """FastAPI dependency for yielding database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
