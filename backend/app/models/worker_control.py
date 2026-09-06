from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base
from datetime import datetime, timezone


class WorkerControl(Base):
    """Worker control actions for active worker management (Phase 6)."""
    __tablename__ = 'worker_controls'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    worker_id = Column(String(length=255), ForeignKey('worker_states.worker_id'), nullable=False, index=True)
    action = Column(String(length=50), nullable=False)  # pause, resume, retire
    requested_by = Column(UUID(as_uuid=True), nullable=False)
    requested_at = Column(DateTime(timezone=True), nullable=False)
    reason = Column(String(255), nullable=True)
    status = Column(String(length=50), default='pending', nullable=False)  # pending, executed, failed
    executed_at = Column(DateTime(timezone=True), nullable=True)

    worker = relationship("WorkerState", foreign_keys=[worker_id])

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'worker_id': self.worker_id,
            'action': self.action,
            'requested_by': str(self.requested_by),
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'reason': self.reason,
            'status': self.status,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
        }