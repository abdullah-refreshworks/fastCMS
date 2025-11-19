"""
Security utilities for password hashing and JWT token management.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context with bcrypt (cost factor 10 for compatibility)
# Lower rounds to avoid initialization issues with some bcrypt versions
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=10,
    bcrypt__ident="2b",  # Use 2b identifier for better compatibility
)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Bcrypt has a 72-byte limit, so we truncate to ensure compatibility.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    # Bcrypt has a max length of 72 bytes - truncate the string (not bytes)
    # Passlib expects a string, not bytes
    password_truncated = password[:72]
    return pwd_context.hash(password_truncated)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hashed password.

    Bcrypt has a 72-byte limit, so we truncate to ensure compatibility.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    # Bcrypt has a max length of 72 bytes - truncate the string (not bytes)
    # Passlib expects a string, not bytes
    password_truncated = plain_password[:72]
    return pwd_context.verify(password_truncated, hashed_password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary of data to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Dictionary of data to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string to decode

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_token_type(payload: Dict[str, Any], expected_type: str) -> bool:
    """
    Verify that a token payload has the expected type.

    Args:
        payload: Decoded token payload
        expected_type: Expected token type ('access' or 'refresh')

    Returns:
        True if token type matches, False otherwise
    """
    return payload.get("type") == expected_type
