"""Project model — NexusForge project definitions and configurations.

Phase 6 — Final Migration & Handover
Projects contain metadata, agent roles, and execution contexts.
"""

from typing import Optional
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base
from pydantic import BaseModel


class Project(Base):
    """Project model for NexusForge project management."""
    __tablename__ = 'projects'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), default='active', nullable=False)  # active, archived, completed
    owner_id = Column(UUID(as_uuid=True), nullable=True)  # User ID who owns the project
    visibility = Column(String(50), default='private', nullable=False)  # private, public
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    settings = Column(JSON, default=dict, nullable=True)  # UI preferences, agent configs, etc.

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id])
    tasks = relationship("Task", back_populates="project")
    artifacts = relationship("Artifact", back_populates="project")
    workers = relationship("Worker", back_populates="project")

    def __repr__(self):
        return f'<Project {self.name}>'


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