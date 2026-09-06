"""Approval Center API routes for human approval of privileged/dangerous agent actions.

Phase 5.6 — Human Approval System
- Request approval for privileged actions
- View pending approvals
- Approve/reject/cancel approvals
- View approval history
- Verify agent identity and reasoning
- Show potential risks and impact
- Enforce expiration
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db import get_db_session
from app.models.approval import ApprovalRequest, ApprovalStatus
from app.schemas.approval import ApprovalCreate, ApprovalUpdate, ApprovalResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/approvals", tags=["approval", "security"])


@router.post("/request", response_model=ApprovalResponse, status_code=status.HTTP_201_CREATED, summary="Create approval request")
async def create_approval_request(
    data: ApprovalCreate,
    db_session: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
):
    """Request human approval for a privileged/dangerous agent action.
    
    The UI must clearly show:
    - Requesting agent name and role
    - Action details (description)
    - Reasoning (why the action is needed)
    - Potential risks and impact
    - Requested timestamp
    - Expiration
    """
    from uuid import uuid4
    
    approval = ApprovalRequest(
        id=str(uuid4()),
        execution_id=data.execution_id or str(uuid4()),
        agent_name=data.agent_name or current_user.get("username", "Unknown Agent"),
        agent_role=data.agent_role or "agent",
        action_type=data.action_type,
        action_description=data.action_description,
        reasoning=data.reasoning,
        potential_impact=data.potential_impact,
        requires_human_approval=True,
        status=ApprovalStatus.PENDING.value,
        requested_by=str(current_user.get("id", "anonymous")),
        requested_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24) if not data.expires_at else datetime.fromisoformat(data.expires_at),
    )
    
    db_session.add(approval)
    await db_session.commit()
    await db_session.refresh(approval)
    
    return approval.to_dict()


@router.get("/pending", response_model=List[ApprovalResponse], summary="List pending approvals")
async def list_pending_approvals(
    db_session: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
):
    """List all pending approval requests visible to the user.
    
    The UI must clearly show for each:
    - Agent name and role
    - Action details
    - Reasoning (why needed)
    - Potential risks
    - Time remaining before expiration
    """
    options = [
        ApprovalStatus.PENDING.value,
    ]
    
    result = await db_session.execute(
        select(ApprovalRequest).where(
            and_(
                ApprovalRequest.status.in_(options),
                ApprovalRequest.expires_at > datetime.now(timezone.utc) if hasattr(ApprovalRequest, "expires_at") else True,
            )
        )
        .order_by(ApprovalRequest.requested_at.desc())
    )
    approvals = result.scalars().all()
    return [approval.to_dict() for approval in approvals]


@router.get("/history", response_model=List[ApprovalResponse], summary="List approval history")
async def list_approval_history(
    execution_id: Optional[str] = None,
    db_session: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
):
    """List approval history for audit.
    
    Shows all approvals with outcomes.
    Useful for tracking which actions were approved/rejected.
    """
    conditions = []
    if execution_id:
        conditions.append(ApprovalRequest.execution_id == execution_id)
    
    if conditions:
        result = await db_session.execute(
            select(ApprovalRequest).where(
                and_(*conditions) if len(conditions) > 1 else conditions[0]
            ).order_by(ApprovalRequest.requested_at.desc())
        )
    else:
        result = await db_session.execute(
            select(ApprovalRequest).order_by(ApprovalRequest.requested_at.desc())
        )
    approvals = result.scalars().all()
    return [approval.to_dict() for approval in approvals]


@router.post("/{approval_id}/approve", response_model=ApprovalResponse, summary="Approve approval request")
async def approve_request(
    approval_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
):
    """Approve an approval request.
    
    After approval, the execution can proceed.
    The UI shows:
    - Who approved (username)
    - When approved
    - The action that was approved
    """
    result = await db_session.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    if approval.status != ApprovalStatus.PENDING.value:
        raise HTTPException(status_code=400, detail="Approval request is not pending")
    
    if approval.is_expired:
        raise HTTPException(status_code=410, detail="Approval request has expired")
    
    approval.status = ApprovalStatus.APPROVED.value
    approval.approved_by = str(current_user.get("id", "anonymous"))
    approval.approved_at = datetime.now(timezone.utc)
    
    await db_session.commit()
    await db_session.refresh(approval)
    
    return approval.to_dict()


@router.post("/{approval_id}/reject", response_model=ApprovalResponse, summary="Reject approval request")
async def reject_request(
    approval_id: str,
    data: dict = None,
    db_session: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
):
    """Reject an approval request.
    
    Shows:
    - Action that was rejected
    - Reason for rejection (optional)
    - Who rejected
    """
    result = await db_session.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    if approval.status != ApprovalStatus.PENDING.value:
        raise HTTPException(status_code=400, detail="Approval request is not pending")
    
    approval.status = ApprovalStatus.REJECTED.value
    approval.rejected_by = str(current_user.get("id", "anonymous"))
    approval.rejection_reason = (data or {}).get("reason", "Rejected by user")
    approval.updated_at = datetime.now(timezone.utc)
    
    await db_session.commit()
    await db_session.refresh(approval)
    
    return approval.to_dict()


@router.post("/{approval_id}/cancel", response_model=ApprovalResponse, summary="Cancel approval request")
async def cancel_request(
    approval_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
):
    """Cancel an approval request.
    
    Allows agents to withdraw approval requests.
    """
    result = await db_session.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    if approval.status not in [ApprovalStatus.PENDING.value, ApprovalStatus.REVIEWING.value]:
        raise HTTPException(status_code=400, detail="Can only cancel pending/reviewing approvals")
    
    approval.status = ApprovalStatus.CANCELLED.value
    approval.cancellation_reason = "Cancelled by agent/user"
    approval.updated_at = datetime.now(timezone.utc)
    
    await db_session.commit()
    await db_session.refresh(approval)
    
    return approval.to_dict()


@router.get("/{approval_id}", response_model=ApprovalResponse, summary="Get approval details")
async def get_approval(
    approval_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
):
    """Get full details of an approval request.
    
    Shows all context: agent info, reasoning, risks, history.
    """
    result = await db_session.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    return approval.to_dict()


@router.get("/my-pending", response_model=List[ApprovalResponse], summary="List my pending approvals")
async def list_my_pending(
    db_session: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
):
    """List approvals requested by the current user."""
    user_id = str(current_user.get("id", "unknown"))
    result = await db_session.execute(
        select(ApprovalRequest).where(
            and_(
                ApprovalRequest.requested_by == user_id,
                ApprovalRequest.status == ApprovalStatus.PENDING.value
            )
        ).order_by(ApprovalRequest.requested_at.desc())
    )
    approvals = result.scalars().all()
    return [approval.to_dict() for approval in approvals]