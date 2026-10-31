import sys
from pathlib import Path

# Ensure backend directory is in sys.path for direct module resolution
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Ensure root backend packages map properly to sys.modules
import backend.database
import backend.models
import backend.models.user

sys.modules.setdefault("database", backend.database)
sys.modules.setdefault("models", backend.models)
sys.modules.setdefault("models.user", backend.models.user)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
<<<<<<< HEAD
    from backend.routers.auth import router as auth_router
except ImportError:
    from routers.auth import router as auth_router

try:
    from backend.routers.intelligence import router as intelligence_router
except ImportError:
    from routers.intelligence import router as intelligence_router

try:
    from backend.routers.operations import router as operations_router
except ImportError:
    from routers.operations import router as operations_router
=======
    from routers.auth import router as auth_router
except ModuleNotFoundError:
    from backend.routers.auth import router as auth_router
>>>>>>> 513bdb13da22d46561a8eb025f27f08d0ef241f5

app = FastAPI(
    title="SubscriptIQ Subscription Management API",
    description="Backend API for Subscription Management, Billing, Finance, and Authentication",
    version="1.0.0",
)

# CORS configuration for React + Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(intelligence_router)
app.include_router(operations_router)


@app.on_event("startup")
def on_startup():
    """Ensure database tables and initial demonstration records exist."""
    try:
        from backend.database import SessionLocal
        from backend.services.demo_seeder import seed_demo_data_if_empty
        db = SessionLocal()
        try:
            seed_demo_data_if_empty(db, force=False)
        finally:
            db.close()
    except Exception as e:
        print(f"[STARTUP NOTICE] Demo seeder completed with notice: {e}")


@app.get("/")
def home():
    return {"message": "SubscriptIQ API is running!", "status": "online"}

