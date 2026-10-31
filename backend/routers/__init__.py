<<<<<<< HEAD
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

=======
try:
    from routers.auth import router as auth_router
except ModuleNotFoundError:
    from backend.routers.auth import router as auth_router
>>>>>>> 513bdb13da22d46561a8eb025f27f08d0ef241f5

