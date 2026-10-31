import sys

try:
    import backend.models.user
    sys.modules.setdefault("models.user", backend.models.user)
    from backend.routers.auth import router as auth_router
    from backend.routers.intelligence import router as intelligence_router
    from backend.routers.operations import router as operations_router
except ImportError:
    from routers.auth import router as auth_router
    from routers.intelligence import router as intelligence_router
    from routers.operations import router as operations_router

__all__ = ["auth_router", "intelligence_router", "operations_router"]


