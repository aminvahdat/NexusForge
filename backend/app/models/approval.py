from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.base import Base


class ApprovalRequest(Base):
    """Human approval request for privileged/dangerous agent actions."""
    
    __tablename__ = "approval_requests"
    
    id = Column(String, primary_key=True)
    execution_id = Column(String, ForeignKey("executions.id"), nullable=False, index=True)
    agent_name = Column(String, nullable=False)
    agent_role = Column(String, nullable=False)
    action_type = Column(String, nullable=False, index=True)
    action_description = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=False)
    potential_risk = Column(Text, nullable=False, default="")
    requires_human_approval = Column(Boolean, default=True, nullable=False)
    status = Column(String, nullable=False, default="pending", index=True)
    requested_by = Column(String, nullable=False, index=True)
    requested_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by = Column(String, nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    cancelled_by = Column(String, nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    execution = relationship("Execution", back_populates="approval_requests")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "agent_name": self.agent_name,
            "agent_role": self.agent_role,
            "action_type": self.action_type,
            "action_description": self.action_description,
            "reasoning": self.reasoning,
            "potential_risk": self.potential_risk,
            "requires_human_approval": self.requires_human_approval,
            "status": self.status,
            "requested_by": self.requested_by,
            "requested_at": self.requested_at.isoformat() if self.requested_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejected_by": self.rejected_by,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "rejection_reason": self.rejection_reason,
            "cancelled_by": self.cancelled_by,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "cancellation_reason": self.cancellation_reason,
            "updated_at": self.updated_at.isoformat(),
        }
    
    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_pending(self) -> bool:
        return self.status == "pending" and not self.is_expired