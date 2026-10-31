try:
    from backend.schemas.auth import (
        UserRegisterRequest,
        UserLoginRequest,
        TokenResponse,
        UserProfileResponse,
        ForgotPasswordRequest,
        ResetPasswordRequest,
        MessageResponse,
    )
except ModuleNotFoundError:
    from schemas.auth import (
        UserRegisterRequest,
        UserLoginRequest,
        TokenResponse,
        UserProfileResponse,
        ForgotPasswordRequest,
        ResetPasswordRequest,
        MessageResponse,
    )

__all__ = [
    "UserRegisterRequest",
    "UserLoginRequest",
    "TokenResponse",
    "UserProfileResponse",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "MessageResponse",
]
