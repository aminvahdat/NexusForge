"""Authorization module for NexusForge — Ownership verification and access control."""

from typing import Optional, Union
import uuid
from fastapi import Depends, HTTPException, status

from app.models import User
from app.auth import get_current_user


def check_ownership(resource_owner_id: Union[str, uuid.UUID, None], user: User) -> bool:
    """Verify if user owns the resource or is a superuser.
    
    FAILS CLOSED:
    Returns True ONLY if user is a superuser OR resource_owner_id matches user.id.
    Never matches arbitrary strings like 'admin'.
    """
    if not user or not user.is_active:
        return False
    if getattr(user, "is_superuser", False):
        return True
    if not resource_owner_id:
        return False
    return str(resource_owner_id) == str(user.id)


def enforce_ownership(
    resource_owner_id: Union[str, uuid.UUID, None],
    user: User,
    resource_name: str = "resource",
) -> None:
    """Enforce ownership or raise 403 Forbidden."""
    if not check_ownership(resource_owner_id, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: You do not have permission to access this {resource_name}",
        )


async def require_superuser(user: User = Depends(get_current_user)) -> User:
    """Dependency: require user to be an active superuser."""
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Administrative privileges required",
        )
    return user
