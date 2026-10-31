from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

try:
    from backend.database import get_db
    from backend.models.user import User, PasswordResetToken
    from backend.schemas.auth import (
        UserRegisterRequest,
        UserLoginRequest,
        TokenResponse,
        UserProfileResponse,
        ForgotPasswordRequest,
        ResetPasswordRequest,
        MessageResponse,
    )
    from backend.core.security import (
        hash_password,
        verify_password,
        create_access_token,
        decode_access_token,
        generate_reset_token,
        hash_reset_token,
    )
    from backend.services.email_service import send_password_reset_email
    from backend.config import settings
except ModuleNotFoundError:
    from database import get_db
    from models.user import User, PasswordResetToken
    from schemas.auth import (
        UserRegisterRequest,
        UserLoginRequest,
        TokenResponse,
        UserProfileResponse,
        ForgotPasswordRequest,
        ResetPasswordRequest,
        MessageResponse,
    )
    from core.security import (
        hash_password,
        verify_password,
        create_access_token,
        decode_access_token,
        generate_reset_token,
        hash_reset_token,
    )
    from services.email_service import send_password_reset_email
    from config import settings

router = APIRouter()
security_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Dependency to extract and verify the current authenticated user from Bearer JWT."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Note: user.id in database is integer or string depending on column type, query safely
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        # Also try converting to int if user_id is numeric string
        try:
            int_id = int(user_id)
            user = db.query(User).filter(User.id == int_id, User.is_active == True).first()
        except (ValueError, TypeError):
            pass

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/register", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)) -> UserProfileResponse:
    """
    Registers a new user account:
    - Validates email and name.
    - Validates password complexity.
    - Hashes password using Argon2.
    - Prevents duplicate email accounts (case-insensitive).
    - Returns serialized user profile (never returns hashed_password).
    """
    normalized_email = request.email.lower()
    existing_user = db.query(User).filter(User.email.ilike(normalized_email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    hashed_pw = hash_password(request.password)
    user = User(
        name=request.name,
        email=normalized_email,
        hashed_password=hashed_pw,
        is_active=True,
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return UserProfileResponse.model_validate(user)
    except Exception as exc:
        db.rollback()
        # Handle database-level duplicate email race conditions safely
        if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user due to a database error.",
        )


@router.post("/login", response_model=TokenResponse)
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates user and issues a signed JWT token.
    Generic error returned for non-existent users or bad passwords to prevent enumeration.
    """
    normalized_email = request.email.lower()
    user = db.query(User).filter(User.email.ilike(normalized_email)).first()

    if not user or not user.is_active or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserProfileResponse)
def get_profile(current_user: User = Depends(get_current_user)) -> UserProfileResponse:
    """Returns profile information for the authenticated user without password hashes."""
    return UserProfileResponse.model_validate(current_user)


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Initiates password reset flow:
    - Never reveals whether an email is registered (uniform success message).
    - If user exists, generates an unguessable reset token.
    - Stores ONLY SHA-256 hash with expiration.
    - Delivers reset link via background email task.
    """
    normalized_email = request.email.lower()
    user = db.query(User).filter(User.email.ilike(normalized_email)).first()

    if user and user.is_active:
        raw_token = generate_reset_token()
        token_hash = hash_reset_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)

        try:
            # Invalidate previous unused reset tokens for this user
            db.query(PasswordResetToken).filter(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used == False,
            ).update({"used": True})

            reset_entry = PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
                used=False,
            )
            db.add(reset_entry)
            db.commit()

            # Dispatch email asynchronously in background
            background_tasks.add_task(send_password_reset_email, user.email, raw_token)
        except Exception:
            db.rollback()

    return MessageResponse(
        message="If this email is registered in our system, you will receive a password reset link shortly."
    )


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Resets password using a single-use, unexpired token:
    - Verifies token hash.
    - Ensures token has not been used and not expired.
    - Hashes new password with Argon2.
    - Marks token as used.
    """
    token_hash = hash_reset_token(request.token)
    reset_entry = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()

    now = datetime.now(timezone.utc)
    if not reset_entry or reset_entry.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used password reset token.",
        )

    # Compare aware datetimes
    entry_expires = reset_entry.expires_at
    if entry_expires.tzinfo is None:
        entry_expires = entry_expires.replace(tzinfo=timezone.utc)

    if entry_expires < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has expired.",
        )

    user = db.query(User).filter(User.id == reset_entry.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or inactive.",
        )

    user.hashed_password = hash_password(request.new_password)
    reset_entry.used = True
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password.",
        )

    return MessageResponse(message="Password has been successfully updated.")
