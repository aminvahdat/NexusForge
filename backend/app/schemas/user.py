"""Pydantic schemas for NexusForge user accounts and authentication."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for registering a new user."""
    email: str = Field(..., description="User email address")
    username: Optional[str] = Field(None, min_length=2, max_length=50)
    password: str = Field(..., min_length=8, description="Plaintext password")
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login credentials."""
    email: str
    password: str


class UserResponse(BaseModel):
    """Schema for user responses."""
    id: str
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT access token."""
    access_token: str
    token_type: str = "bearer"
