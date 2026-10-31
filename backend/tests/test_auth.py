import pytest
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, BackgroundTasks
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models.user import User, PasswordResetToken
from backend.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from backend.routers.auth import register, login, get_profile, forgot_password, reset_password
from backend.core.security import (
    hash_password,
    verify_password,
    validate_password_complexity,
    hash_reset_token,
    create_access_token,
    decode_access_token,
)


@pytest.fixture(scope="function")
def db_session():
    """Isolated in-memory database fixture to prevent modifying production Supabase data."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ----------------------------------------------------
# 1. Successful Registration
# ----------------------------------------------------
def test_successful_registration(db_session):
    req = UserRegisterRequest(
        name="John Doe",
        email="john@example.com",
        password="ValidPassword#123",
    )
    user = register(req, db=db_session)
    assert user.id is not None
    assert user.name == "John Doe"
    assert user.email == "john@example.com"
    assert user.is_active is True


# ----------------------------------------------------
# 2. Duplicate Email Registration (Case-Insensitive)
# ----------------------------------------------------
def test_duplicate_email_registration(db_session):
    req1 = UserRegisterRequest(
        name="John Doe",
        email="john@example.com",
        password="ValidPassword#123",
    )
    register(req1, db=db_session)

    req2 = UserRegisterRequest(
        name="John Different",
        email="JOHN@EXAMPLE.COM",
        password="AnotherPassword#456",
    )
    with pytest.raises(HTTPException) as exc_info:
        register(req2, db=db_session)
    assert exc_info.value.status_code == 400
    assert "already exists" in exc_info.value.detail.lower()


# ----------------------------------------------------
# 3. Invalid Email Format
# ----------------------------------------------------
def test_invalid_email_format():
    with pytest.raises(Exception):
        UserRegisterRequest(
            name="Bad Email",
            email="not-an-email",
            password="ValidPassword#123",
        )


# ----------------------------------------------------
# 4. Password Shorter Than Required (<= 8)
# ----------------------------------------------------
def test_password_shorter_than_required():
    with pytest.raises(ValueError, match="longer than 8 characters"):
        validate_password_complexity("Ab1!cde")  # 7 chars
    with pytest.raises(ValueError, match="longer than 8 characters"):
        validate_password_complexity("Ab1!cdef")  # 8 chars (must be > 8)


# ----------------------------------------------------
# 5. Password Without Uppercase Letters
# ----------------------------------------------------
def test_password_without_uppercase():
    with pytest.raises(ValueError, match="uppercase"):
        validate_password_complexity("lowercase123!")


# ----------------------------------------------------
# 6. Password Without Lowercase Letters
# ----------------------------------------------------
def test_password_without_lowercase():
    with pytest.raises(ValueError, match="lowercase"):
        validate_password_complexity("UPPERCASE123!")


# ----------------------------------------------------
# 7. Password Without Special Characters
# ----------------------------------------------------
def test_password_without_special_characters():
    with pytest.raises(ValueError, match="special character"):
        validate_password_complexity("NoSpecialChar123")


# ----------------------------------------------------
# 8. Successful Login
# ----------------------------------------------------
def test_successful_login(db_session):
    req = UserRegisterRequest(
        name="Alice Smith",
        email="alice@example.com",
        password="SecurePassword#2026",
    )
    register(req, db=db_session)

    login_req = UserLoginRequest(email="alice@example.com", password="SecurePassword#2026")
    token_resp = login(login_req, db=db_session)
    assert token_resp.access_token is not None
    assert token_resp.token_type == "bearer"


# ----------------------------------------------------
# 9. Incorrect Password
# ----------------------------------------------------
def test_login_incorrect_password(db_session):
    req = UserRegisterRequest(
        name="Alice Smith",
        email="alice@example.com",
        password="SecurePassword#2026",
    )
    register(req, db=db_session)

    login_req = UserLoginRequest(email="alice@example.com", password="WrongPassword#2026")
    with pytest.raises(HTTPException) as exc_info:
        login(login_req, db=db_session)
    assert exc_info.value.status_code == 401
    assert "Invalid email or password" in exc_info.value.detail


# ----------------------------------------------------
# 10. Login with Nonexistent Email
# ----------------------------------------------------
def test_login_nonexistent_email(db_session):
    login_req = UserLoginRequest(email="nonexistent@example.com", password="SecurePassword#2026")
    with pytest.raises(HTTPException) as exc_info:
        login(login_req, db=db_session)
    assert exc_info.value.status_code == 401
    assert "Invalid email or password" in exc_info.value.detail


# ----------------------------------------------------
# 11. JWT Token Verification
# ----------------------------------------------------
def test_jwt_token_verification(db_session):
    req = UserRegisterRequest(
        name="Bob Builder",
        email="bob@example.com",
        password="SecurePassword#2026",
    )
    register(req, db=db_session)

    token_resp = login(UserLoginRequest(email="bob@example.com", password="SecurePassword#2026"), db=db_session)
    payload = decode_access_token(token_resp.access_token)
    assert payload is not None
    assert payload["email"] == "bob@example.com"
    assert "exp" in payload

    # Invalid token check
    assert decode_access_token("invalid.token.signature") is None


# ----------------------------------------------------
# 12. Access to Protected Endpoints (/auth/me)
# ----------------------------------------------------
def test_access_to_protected_endpoint(db_session):
    req = UserRegisterRequest(
        name="Charlie Brown",
        email="charlie@example.com",
        password="CharliePassword#123",
    )
    user = register(req, db=db_session)
    profile = get_profile(current_user=user)
    assert profile.email == "charlie@example.com"
    assert profile.name == "Charlie Brown"
    # Never expose hashed_password in response schema
    assert not hasattr(profile, "hashed_password")


# ----------------------------------------------------
# 13. Forgot-Password Request (Uniform Response)
# ----------------------------------------------------
def test_forgot_password_request_uniform_response(db_session):
    req = UserRegisterRequest(
        name="Dana Scully",
        email="dana@example.com",
        password="DanaPassword#123",
    )
    register(req, db=db_session)

    bg = BackgroundTasks()
    res1 = forgot_password(ForgotPasswordRequest(email="dana@example.com"), background_tasks=bg, db=db_session)
    res2 = forgot_password(ForgotPasswordRequest(email="notfound@example.com"), background_tasks=bg, db=db_session)

    assert res1.message == res2.message
    assert "If this email is registered" in res1.message


# ----------------------------------------------------
# 14. Invalid Reset Token
# ----------------------------------------------------
def test_password_reset_invalid_token(db_session):
    reset_req = ResetPasswordRequest(token="completely-bogus-token", new_password="NewSecurePass#2026")
    with pytest.raises(HTTPException) as exc_info:
        reset_password(reset_req, db=db_session)
    assert exc_info.value.status_code == 400
    assert "Invalid or already used" in exc_info.value.detail


# ----------------------------------------------------
# 15. Expired Reset Token
# ----------------------------------------------------
def test_password_reset_expired_token(db_session):
    req = UserRegisterRequest(
        name="Evan",
        email="evan@example.com",
        password="OldPassword#123",
    )
    register(req, db=db_session)

    bg = BackgroundTasks()
    forgot_password(ForgotPasswordRequest(email="evan@example.com"), background_tasks=bg, db=db_session)

    token_entry = db_session.query(PasswordResetToken).first()
    raw_token = "expired-token-sample"
    token_entry.token_hash = hash_reset_token(raw_token)
    token_entry.expires_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    db_session.commit()

    reset_req = ResetPasswordRequest(token=raw_token, new_password="NewSecurePassword#2026")
    with pytest.raises(HTTPException) as exc_info:
        reset_password(reset_req, db=db_session)
    assert exc_info.value.status_code == 400
    assert "expired" in exc_info.value.detail.lower()


# ----------------------------------------------------
# 16. Successful Password Reset
# ----------------------------------------------------
def test_successful_password_reset(db_session):
    req = UserRegisterRequest(
        name="Fiona",
        email="fiona@example.com",
        password="OldPassword#123",
    )
    register(req, db=db_session)

    bg = BackgroundTasks()
    forgot_password(ForgotPasswordRequest(email="fiona@example.com"), background_tasks=bg, db=db_session)

    token_entry = db_session.query(PasswordResetToken).first()
    raw_token = "valid-reset-token-sample"
    token_entry.token_hash = hash_reset_token(raw_token)
    token_entry.expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    db_session.commit()

    reset_req = ResetPasswordRequest(token=raw_token, new_password="NewSecurePassword#2026")
    res = reset_password(reset_req, db=db_session)
    assert "successfully updated" in res.message

    # Login with new password succeeds
    login_resp = login(UserLoginRequest(email="fiona@example.com", password="NewSecurePassword#2026"), db=db_session)
    assert login_resp.access_token is not None

    # Login with old password fails
    with pytest.raises(HTTPException):
        login(UserLoginRequest(email="fiona@example.com", password="OldPassword#123"), db=db_session)


# ----------------------------------------------------
# 17. Reusing an Already-Used Reset Token
# ----------------------------------------------------
def test_reusing_already_used_reset_token(db_session):
    req = UserRegisterRequest(
        name="George",
        email="george@example.com",
        password="OldPassword#123",
    )
    register(req, db=db_session)

    bg = BackgroundTasks()
    forgot_password(ForgotPasswordRequest(email="george@example.com"), background_tasks=bg, db=db_session)

    token_entry = db_session.query(PasswordResetToken).first()
    raw_token = "single-use-token-sample"
    token_entry.token_hash = hash_reset_token(raw_token)
    token_entry.expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    db_session.commit()

    # First use succeeds
    reset_req = ResetPasswordRequest(token=raw_token, new_password="NewSecurePassword#2026")
    reset_password(reset_req, db=db_session)

    # Second use fails
    with pytest.raises(HTTPException) as exc_info:
        reset_password(reset_req, db=db_session)
    assert exc_info.value.status_code == 400
    assert "Invalid or already used" in exc_info.value.detail


# ----------------------------------------------------
# 18. Verify Passwords are Stored as Hashes
# ----------------------------------------------------
def test_verify_passwords_are_stored_as_argon2_hashes(db_session):
    raw_password = "SecretPassword!2026"
    req = UserRegisterRequest(
        name="Hannah",
        email="hannah@example.com",
        password=raw_password,
    )
    user = register(req, db=db_session)

    stored_user = db_session.query(User).filter(User.id == user.id).first()
    assert stored_user.hashed_password != raw_password
    assert raw_password not in stored_user.hashed_password
    assert stored_user.hashed_password.startswith("$argon2")
    assert verify_password(raw_password, stored_user.hashed_password) is True
