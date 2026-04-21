"""Security utilities - JWT, password hashing, 2FA."""

from datetime import datetime, timedelta, timezone
from typing import Any

import pyotp
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create JWT access token.

    Args:
        data: Payload data (should include sub, tenant_id, role, email, plan)
        expires_delta: Custom expiration time

    Returns:
        Encoded JWT token
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


def create_refresh_token(data: dict[str, Any]) -> str:
    """
    Create JWT refresh token.

    Args:
        data: Payload data (minimal - just user_id)

    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and verify JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload

    Raises:
        JWTError: If token is invalid or expired
    """
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    return payload


# 2FA (TOTP)
def generate_totp_secret() -> str:
    """Generate a new TOTP secret for 2FA."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str, issuer: str = "AltCare") -> str:
    """
    Get TOTP provisioning URI for QR code generation.

    Args:
        secret: TOTP secret
        email: User email
        issuer: Application name

    Returns:
        TOTP URI (otpauth://...)
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)


def verify_totp(secret: str, token: str) -> bool:
    """
    Verify TOTP token.

    Args:
        secret: User's TOTP secret
        token: 6-digit code from authenticator app

    Returns:
        True if valid, False otherwise
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)  # Allow 1 step tolerance
