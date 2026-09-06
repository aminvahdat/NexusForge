from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base
from datetime import datetime, timezone


class WorkerState(Base):
    """Worker state tracking for active worker control (Phase 6)."""
    __tablename__ = 'worker_states'

    worker_id = Column(String(length=255), primary_key=True, nullable=False)
    hostname = Column(String(length=255), nullable=True)
    status = Column(String(length=50), default='idle', nullable=False, index=True)
    current_task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id'), nullable=True)
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    meta_info = Column(JSON, default=dict)

    def to_dict(self) -> dict:
        return {
            'worker_id': self.worker_id,
            'hostname': self.hostname,
            'status': self.status,
            'current_task_id': str(self.current_task_id) if self.current_task_id else None,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'meta_info': self.meta_info,
        }