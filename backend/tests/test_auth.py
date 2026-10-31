import sys
from pathlib import Path
import pytest
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, BackgroundTasks
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from database import Base
from models.user import User, PasswordResetToken
from schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from routers.auth import register, login, get_profile, forgot_password, reset_password
from core.security import (
    hash_password,
    verify_password,
    validate_password_complexity,
    hash_reset_token,
    create_access_token,
    decode_access_token,
)


@pytest.fixture(scope="function")
def db_session():
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
# 1. Password Complexity & Argon2 Hashing
# ----------------------------------------------------

def test_password_complexity_valid():
    validate_password_complexity("StrongP@ss123")


@pytest.mark.parametrize(
    "bad_password, expected_error",
    [
        ("Sh0!rt", "longer than 8 characters"),
        ("Exact8!a", "longer than 8 characters"),
        ("alllowercase123!", "uppercase"),
        ("ALLUPPERCASE123!", "lowercase"),
        ("NoSpecialChar123", "special character"),
    ],
)
def test_password_complexity_invalid(bad_password, expected_error):
    with pytest.raises(ValueError, match=expected_error):
        validate_password_complexity(bad_password)


def test_argon2_hashing():
    raw_pass = "MySecret#2026"
    hashed = hash_password(raw_pass)
    assert hashed.startswith("$argon2")
    assert raw_pass not in hashed
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongSecret#2026", hashed) is False


# ----------------------------------------------------
# 2. Registration Scenarios
# ----------------------------------------------------

def test_registration_success(db_session):
    req = UserRegisterRequest(
        name="Alice Walker",
        email="alice@example.com",
        password="ValidPassword#123",
    )
    user = register(req, db=db_session)
    assert user.id is not None
    assert user.name == "Alice Walker"
    assert user.email == "alice@example.com"
    assert user.hashed_password.startswith("$argon2")


def test_registration_duplicate_email(db_session):
    req1 = UserRegisterRequest(
        name="Alice One",
        email="alice@example.com",
        password="ValidPassword#123",
    )
    register(req1, db=db_session)

    req2 = UserRegisterRequest(
        name="Alice Two",
        email="ALICE@EXAMPLE.COM",
        password="AnotherValidPassword#456",
    )
    with pytest.raises(HTTPException) as exc_info:
        register(req2, db=db_session)
    assert exc_info.value.status_code == 400
    assert "already exists" in exc_info.value.detail.lower()


# ----------------------------------------------------
# 3. Login & JWT Authentication Scenarios
# ----------------------------------------------------

def test_login_success(db_session):
    req = UserRegisterRequest(
        name="Bob Builder",
        email="bob@example.com",
        password="BobPassword@999",
    )
    register(req, db=db_session)

    login_req = UserLoginRequest(email="bob@example.com", password="BobPassword@999")
    token_resp = login(login_req, db=db_session)
    assert token_resp.access_token is not None
    assert token_resp.token_type == "bearer"

    # Decode and verify payload
    payload = decode_access_token(token_resp.access_token)
    assert payload is not None
    assert payload["email"] == "bob@example.com"


def test_login_invalid_password(db_session):
    req = UserRegisterRequest(
        name="Bob Builder",
        email="bob@example.com",
        password="BobPassword@999",
    )
    register(req, db=db_session)

    login_req = UserLoginRequest(email="bob@example.com", password="WrongPassword@999")
    with pytest.raises(HTTPException) as exc_info:
        login(login_req, db=db_session)
    assert exc_info.value.status_code == 401
    assert "Invalid email or password" in exc_info.value.detail


def test_login_nonexistent_email(db_session):
    login_req = UserLoginRequest(email="nonexistent@example.com", password="Password#123")
    with pytest.raises(HTTPException) as exc_info:
        login(login_req, db=db_session)
    assert exc_info.value.status_code == 401
    assert "Invalid email or password" in exc_info.value.detail


def test_profile_retrieval(db_session):
    req = UserRegisterRequest(
        name="Charlie Brown",
        email="charlie@example.com",
        password="CharliePassword#123",
    )
    user = register(req, db=db_session)
    profile = get_profile(current_user=user)
    assert profile.id == user.id
    assert profile.email == "charlie@example.com"


# ----------------------------------------------------
# 4. Forgot-Password & Reset Flow Scenarios
# ----------------------------------------------------

def test_forgot_password_uniform_response(db_session):
    req = UserRegisterRequest(
        name="Dana",
        email="dana@example.com",
        password="DanaPassword#123",
    )
    register(req, db=db_session)

    bg = BackgroundTasks()
    res_existing = forgot_password(ForgotPasswordRequest(email="dana@example.com"), background_tasks=bg, db=db_session)
    res_non_existing = forgot_password(ForgotPasswordRequest(email="ghost@example.com"), background_tasks=bg, db=db_session)

    assert res_existing.message == res_non_existing.message


def test_password_reset_success_and_single_use(db_session):
    req = UserRegisterRequest(
        name="Evan",
        email="evan@example.com",
        password="OldPassword#123",
    )
    register(req, db=db_session)

    bg = BackgroundTasks()
    forgot_password(ForgotPasswordRequest(email="evan@example.com"), background_tasks=bg, db=db_session)

    token_entry = db_session.query(PasswordResetToken).first()
    assert token_entry is not None
    assert token_entry.used is False

    raw_token = "single-use-reset-token-sample"
    token_entry.token_hash = hash_reset_token(raw_token)
    db_session.commit()

    # Reset password
    reset_req = ResetPasswordRequest(token=raw_token, new_password="NewSecurePassword#2026")
    res = reset_password(reset_req, db=db_session)
    assert "successfully updated" in res.message

    # Verify single-use rejection
    with pytest.raises(HTTPException) as exc_info:
        reset_password(reset_req, db=db_session)
    assert exc_info.value.status_code == 400
    assert "Invalid or already used" in exc_info.value.detail

    # Verify new password works and old password fails
    assert login(UserLoginRequest(email="evan@example.com", password="NewSecurePassword#2026"), db=db_session)
    with pytest.raises(HTTPException):
        login(UserLoginRequest(email="evan@example.com", password="OldPassword#123"), db=db_session)


def test_password_reset_expired_token(db_session):
    req = UserRegisterRequest(
        name="Fiona",
        email="fiona@example.com",
        password="FionaPassword#123",
    )
    register(req, db=db_session)

    bg = BackgroundTasks()
    forgot_password(ForgotPasswordRequest(email="fiona@example.com"), background_tasks=bg, db=db_session)

    token_entry = db_session.query(PasswordResetToken).first()
    raw_token = "expired-token-sample"
    token_entry.token_hash = hash_reset_token(raw_token)
    token_entry.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    db_session.commit()

    reset_req = ResetPasswordRequest(token=raw_token, new_password="NewSecurePassword#2026")
    with pytest.raises(HTTPException) as exc_info:
        reset_password(reset_req, db=db_session)
    assert exc_info.value.status_code == 400
    assert "expired" in exc_info.value.detail.lower()
