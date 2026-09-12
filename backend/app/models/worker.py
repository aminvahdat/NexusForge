from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from app.models import Worker


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