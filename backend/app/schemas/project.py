"""Pydantic schemas for NexusForge projects."""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from app.models import Project as ProjectModel


class ProjectBase(BaseModel):
    """Base project schema with common fields."""

    name: str = Field(..., max_length=255, description="Project name")
    description: str = Field(..., description="Project description")
    ai_provider: Optional[str] = Field(None, description="AI provider")
    ai_model: Optional[str] = Field(None, description="AI model")
    preferred_language: str = Field(default="en", description="Preferred language")
    timezone: str = Field(default="UTC", description="Timezone")
    telegram_notifications_enabled: bool = Field(default=False, description="Enable Telegram notifications")
    telegram_chat_id: Optional[str] = Field(None, description="Telegram chat ID")

    class Config:
        from_attributes = True


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""

    owner_id: str = Field(..., description="Owner user ID")


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    preferred_language: Optional[str] = None
    timezone: Optional[str] = None
    telegram_notifications_enabled: Optional[bool] = None
    telegram_chat_id: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectResponse(ProjectBase):
    """Schema for project responses."""

    id: str = Field(..., description="Project ID (UUID)")
    owner_id: str = Field(..., description="Owner user ID")
    status: str = Field(..., description="Project status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


def project_from_model(model: ProjectModel) -> ProjectResponse:
    """Convert a Project model to a ProjectResponse."""
    return ProjectResponse(
        id=str(model.id),
        name=model.name,
        description=model.description,
        owner_id=str(model.owner_id),
        status=model.status,
        ai_provider=model.ai_provider,
        ai_model=model.ai_model,
        preferred_language=model.preferred_language,
        timezone=model.timezone,
        telegram_notifications_enabled=model.telegram_notifications_enabled,
        telegram_chat_id=model.telegram_chat_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )