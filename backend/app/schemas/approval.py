"""Pydantic schemas for Approval Center — aligned with Alembic migration 1875b06d6a87."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID


class ApprovalCreate(BaseModel):
    """Create approval request — maps to migration schema."""
    task_id: Optional[str] = None
    action_type: Optional[str] = None
    action_description: Optional[str] = None
    reasoning: Optional[str] = None
    potential_impact: Optional[str] = None
    expires_at: Optional[str] = None


class ApprovalUpdate(BaseModel):
    """Update approval request."""
    status: Optional[str] = None
    rejection_reason: Optional[str] = None
    outcome: Optional[str] = None


class ApprovalResponse(BaseModel):
    """Response for approval request — matches migration schema."""
    id: str
    task_id: str
    requested_by_user_id: str
    action: str
    reason: str
    risk_level: str
    status: str
    requested_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    approved_by_user_id: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    outcome: Optional[str] = None