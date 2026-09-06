"""User model — required by auth.py for authentication.

Phase 6 — Final Migration & Handover
This model is required by backend/app/auth.py which imports:
    from app.models.user import User
"""

from typing import Optional
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base
from pydantic import BaseModel


class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f'<User {self.email}>'


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