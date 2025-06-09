# security.py - Security utilities for FastAPI application
# Handles password hashing, token generation, and JWT operations.

from passlib.context import CryptContext
import secrets
import hashlib
from typing import Optional
from datetime import timedelta

import jwt
from app.config import settings
from app.utils.date import utcnow


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def get_password_hash(password: str) -> str:
    """Generate secure hash for password storage using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed version with timing attack protection."""
    return pwd_context.verify(plain_password, hashed_password)


def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def generate_password_reset_token(user_id: str, timestamp: str) -> str:
    """Generate secure password reset token."""
    data = f"{user_id}:{timestamp}:{secrets.token_urlsafe(16)}"
    return hashlib.sha256(data.encode()).hexdigest()


def verify_password_reset_token(token: str, user_id: str, timestamp: str, max_age_hours: int = 24) -> bool:
    """Verify password reset token validity."""
    from app.utils.date import from_iso
    try:
        # Check if token is expired
        token_time = from_iso(timestamp)
        if utcnow() - token_time > timedelta(hours=max_age_hours):
            return False

        # Regenerate expected token and compare
        expected_token = generate_password_reset_token(user_id, timestamp)
        return secrets.compare_digest(token, expected_token)
    except (ValueError, TypeError):
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = utcnow() + (expires_delta or timedelta(minutes=60))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decode a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")
