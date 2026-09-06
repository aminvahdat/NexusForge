from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ArtifactCreate(BaseModel):
    project_id: str
    task_id: Optional[str] = None
    execution_id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., description="markdown, code, diagram, report, etc.")
    description: Optional[str] = None
    path: Optional[str] = None
    size: Optional[int] = None
    mime_type: Optional[str] = None
    checksum: Optional[str] = None
    is_public: bool = Field(default=False)
    metadata: Optional[dict] = Field(default_factory=dict)


class ArtifactUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    path: Optional[str] = None
    size: Optional[int] = None
    mime_type: Optional[str] = None
    checksum: Optional[str] = None
    is_public: Optional[bool] = None
    metadata: Optional[dict] = None


class ArtifactResponse(BaseModel):
    id: str
    project_id: str
    task_id: Optional[str]
    execution_id: Optional[str]
    name: str
    type: str
    version: int
    description: Optional[str]
    path: Optional[str]
    size: Optional[int]
    mime_type: Optional[str]
    checksum: Optional[str]
    author_id: Optional[str]
    created_at: Optional[str]
    extra_data: Optional[dict]
    is_public: bool


class ArtifactVersion(BaseModel):
    version: int
    name: str
    created_at: str
    author_id: Optional[str]
    size: Optional[int]