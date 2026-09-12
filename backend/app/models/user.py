from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from app.models import User


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    email: str
    username: Optional[str] = None
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user responses."""
    id: str
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime


class Token(BaseModel):
    """Schema for JWT tokens."""
    access_token: str
    token_type: str