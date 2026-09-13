"""Authentication and security utilities for NexusForge.

Enforces fail-closed token validation, database-backed active user verification,
and secure password handling.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config.settings import get_settings
from app.db import get_db_session
from app.models import User
from app.schemas.user import Token, UserCreate, UserResponse

import bcrypt

settings = get_settings()

SECRET_KEY = settings.jwt_secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_access_token_expire_minutes


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


get_password_hash = hash_password


def verify_password(hashed: str, password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def to_uuid(val) -> Optional[uuid.UUID]:
    """Safely convert value to uuid.UUID."""
    if val is None:
        return None
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except (ValueError, AttributeError):
        return None


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token with expiration."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db_session: AsyncSession = Depends(get_db_session),
) -> User:
    """Retrieve and verify current active user from database.
    
    FAILS CLOSED:
    - Missing token -> 401 Unauthorized
    - Expired / malformed token -> 401 Unauthorized
    - Missing user ID / subject -> 401 Unauthorized
    - Non-existent user -> 401 Unauthorized
    - Inactive user -> 401 Unauthorized
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub: str = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: missing subject",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Resolve user by UUID primary key or email
    user_uuid = to_uuid(sub)
    if user_uuid:
        query = select(User).where(User.id == user_uuid)
    else:
        query = select(User).where(User.email == sub.lower())

    result = await db_session.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db_session: AsyncSession = Depends(get_db_session),
) -> Optional[User]:
    """Retrieve current user if a valid token is provided; otherwise return None without raising."""
    if not token:
        return None
    try:
        return await get_current_user(token=token, db_session=db_session)
    except HTTPException:
        return None
