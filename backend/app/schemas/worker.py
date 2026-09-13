"""Pydantic schemas for NexusForge worker instances and telemetry."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class WorkerCreate(BaseModel):
    """Schema for registering a worker."""
    worker_id: str = Field(..., max_length=100)
    hostname: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = None
    skills: List[str] = Field(default_factory=list)


class WorkerResponse(BaseModel):
    """Schema for worker status and info."""
    id: str
    worker_id: str
    hostname: Optional[str] = None
    status: str
    current_task_id: Optional[str] = None
    role: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkerControlRequest(BaseModel):
    """Schema for worker lifecycle control actions (pause, resume, retire)."""
    action: str = Field(..., description="Action to perform: pause, resume, retire")


class WorkerControlResponse(BaseModel):
    worker_id: str
    action: str
    status: str
