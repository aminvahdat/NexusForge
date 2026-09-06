"""Worker model — NexusForge agent workers.

Phase 6 — Final Migration & Handover
Workers are execution resources that run agent tasks.
"""

from typing import Optional
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base
from pydantic import BaseModel


class Worker(Base):
    """Worker model for NexusForge agent workers."""
    __tablename__ = 'workers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    worker_id = Column(String(255), unique=True, nullable=False, index=True)
    hostname = Column(String(255), nullable=True)
    status = Column(String(50), default='idle', nullable=False)  # idle, active, error
    current_task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id'), nullable=True)
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    meta_info = Column(JSON, default=dict, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="workers")

    def __repr__(self):
        return f'<Worker {self.worker_id}>'


class WorkerCreate(BaseModel):
    """Schema for creating a worker."""
    worker_id: str
    hostname: Optional[str] = None
    project_id: Optional[str] = None


class WorkerResponse(BaseModel):
    """Schema for worker responses."""
    id: str
    worker_id: str
    hostname: Optional[str] = None
    status: str
    current_task_id: Optional[str] = None
    last_heartbeat: Optional[str] = None
    started_at: datetime
    updated_at: datetime
    meta_info: dict