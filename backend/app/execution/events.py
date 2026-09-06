from enum import Enum, auto
from datetime import datetime
from typing import Optional, Dict, Any, List


class EventType(Enum):
    EXECUTION_CREATED = auto()
    EXECUTION_QUEUED = auto()
    WORKER_ASSIGNED = auto()
    EXECUTION_STARTED = auto()
    WORKER_ACTIVITY = auto()
    EXECUTION_PROGRESS = auto()
    EXECUTION_COMPLETED = auto()
    EXECUTION_FAILED = auto()
    EXECUTION_CANCELLED = auto()
    WORKER_STARTED = auto()
    WORKER_STOPPED = auto()
    TASK_COMPLETED = auto()
    TASK_FAILED = auto()


class Event:
    def __init__(
        self,
        event_type: EventType,
        message: str,
        execution_id: str,
        worker_id: Optional[str] = None,
        task_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.event_type = event_type
        self.message = message
        self.execution_id = execution_id
        self.worker_id = worker_id
        self.task_id = task_id
        self.timestamp = timestamp or datetime.utcnow()
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.name,
            "message": self.message,
            "execution_id": self.execution_id,
            "worker_id": self.worker_id,
            "task_id": self.task_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }