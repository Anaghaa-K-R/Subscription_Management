from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from routers.auth import router as auth_router
except ModuleNotFoundError:
    from backend.routers.auth import router as auth_router

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


@app.get("/")
def home():
    return {"message": "Backend is running!"}
