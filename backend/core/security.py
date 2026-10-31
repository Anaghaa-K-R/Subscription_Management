import re
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
import jwt

try:
    from config import settings
except ModuleNotFoundError:
    from backend.config import settings

# Argon2 hasher instance with secure default parameters
hasher = PasswordHasher()


def validate_password_complexity(password: str) -> None:
    """
    Validates that password:
    - is longer than 8 characters (> 8)
    - contains at least one uppercase letter
    - contains at least one lowercase letter
    - contains at least one special character
    """
    if len(password) <= 8:
        raise ValueError("Password must be longer than 8 characters.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>[\]\\/'`~_+=; -]", password):
        raise ValueError("Password must contain at least one special character.")


def hash_password(password: str) -> str:
    """Hashes a password using Argon2. Never stores or logs plain text."""
    return hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against an Argon2 hash."""
    try:
        return hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Issues a signed JWT token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None


def generate_reset_token() -> str:
    """Generates a secure, cryptographically random reset token for email delivery."""
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    """Computes SHA-256 hash of a reset token for database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
