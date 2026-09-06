from enum import Enum, auto
from datetime import datetime
from typing import Optional, Dict, Any


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    WORKING = "working"
    BLOCKED = "blocked"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionState:
    def __init__(
        self,
        execution_id: str,
        task_id: str,
        worker_id: Optional[str] = None,
        status: ExecutionStatus = ExecutionStatus.PENDING,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ):
        self.execution_id = execution_id
        self.task_id = task_id
        self.worker_id = worker_id
        self.status = status
        self.started_at = started_at
        self.completed_at = completed_at
        self.result = result
        self.error = error
        self.events: list = []
        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "worker_id": self.worker_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat(),
            "result": self.result,
            "error": self.error,
            "events": len(self.events),
        }
