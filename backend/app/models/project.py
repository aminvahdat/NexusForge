from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from app.models import Project


class ProjectCreate(BaseModel):
    """Schema for creating a project."""
    name: str
    description: Optional[str] = None
    owner_id: Optional[str] = None
    settings: Optional[dict] = None


class ProjectResponse(BaseModel):
    """Schema for project responses."""
    id: str
    name: str
    description: Optional[str] = None
    status: str
    owner_id: Optional[str] = None
    visibility: str
    created_at: datetime
    updated_at: datetime
    settings: dict