from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base


class ApprovalStatus:
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    REVIEWING = "reviewing"


class ApprovalRequest(Base):
    """Approval request model — matches Alembic migration schema.
    
    Columns: id, task_id, requested_by_user_id, action, reason, risk_level,
             status, requested_at, expires_at, approved_by_user_id,
             approved_at, rejection_reason, outcome
    """
    
    __tablename__ = "approval_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True)
    requested_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(255), nullable=False)
    reason = Column(Text, nullable=False)
    risk_level = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="pending", index=True)
    requested_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    approved_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    outcome = Column(String(255), nullable=True)
    
    task = relationship("Task")
    requested_by_user = relationship("User", foreign_keys=[requested_by_user_id])
    approved_by_user = relationship("User", foreign_keys=[approved_by_user_id])
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "task_id": str(self.task_id),
            "requested_by_user_id": str(self.requested_by_user_id),
            "action": self.action,
            "reason": self.reason,
            "risk_level": self.risk_level,
            "status": self.status,
            "requested_at": self.requested_at.isoformat() if self.requested_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "approved_by_user_id": str(self.approved_by_user_id) if self.approved_by_user_id else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejection_reason": self.rejection_reason,
            "outcome": self.outcome,
        }
    
    @property
    def is_expired(self):
        from datetime import datetime, timezone
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at