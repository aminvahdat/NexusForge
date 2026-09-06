from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ApprovalCreate(BaseModel):
    execution_id: Optional[str] = None
    agent_name: Optional[str] = None
    agent_role: Optional[str] = None
    action_type: str = Field(..., description="Type of action requiring approval")
    action_description: str = Field(..., description="Detailed description of the action")
    reasoning: str = Field(..., description="Why this action is needed")
    potential_impact: str = Field(..., description="Potential risks and impact")
    expires_at: Optional[str] = Field(None, description="ISO datetime when approval expires")
    metadata: Optional[dict] = Field(default_factory=dict)


class ApprovalUpdate(BaseModel):
    action_type: Optional[str] = None
    action_description: Optional[str] = None
    reasoning: Optional[str] = None
    potential_impact: Optional[str] = None
    expires_at: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: str
    execution_id: str
    agent_name: str
    agent_role: str
    action_type: str
    action_description: str
    reasoning: str
    potential_impact: str
    requires_human_approval: bool
    status: str
    requested_by: str
    requested_at: Optional[str]
    expires_at: Optional[str]
    approved_by: Optional[str]
    approved_at: Optional[str]
    rejected_by: Optional[str]
    rejected_at: Optional[str]
    rejection_reason: Optional[str]
    cancelled_by: Optional[str]
    cancelled_at: Optional[str]
    cancellation_reason: Optional[str]
    updated_at: str
    is_expired: bool = False
    is_pending: bool = False


class ApprovalSummary(BaseModel):
    id: str
    agent_name: str
    agent_role: str
    action_type: str
    status: str
    requested_at: Optional[str]
    expires_at: Optional[str]
    is_expired: bool
    is_pending: bool
