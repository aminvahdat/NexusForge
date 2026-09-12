from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from app.models import Artifact


class ArtifactCreate(BaseModel):
    """Schema for creating an artifact."""
    name: str
    description: Optional[str] = None
    content_type: Optional[str] = None
    storage_path: str
    task_id: Optional[str] = None
    execution_id: Optional[str] = None
    version: str = '1.0'


class ArtifactResponse(BaseModel):
    """Schema for artifact responses."""
    id: str
    name: str
    description: Optional[str] = None
    content_type: Optional[str] = None
    storage_path: str
    task_id: Optional[str] = None
    execution_id: Optional[str] = None
    version: str
    created_at: datetime
    updated_at: datetime
    meta_info: dict