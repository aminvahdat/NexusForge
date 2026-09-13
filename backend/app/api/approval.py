"""Approval Center API routes for human approval of privileged/dangerous agent actions."""

from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import uuid4
import uuid
from fastapi import APIRouter, HTTPException, Depends, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db import get_db_session
from app.models import ApprovalRequest, User
from app.schemas.approval import ApprovalCreate, ApprovalUpdate, ApprovalResponse
from app.auth import get_current_user

router = APIRouter(prefix="/approvals", tags=["approval", "security"])


def to_uuid(val) -> Optional[uuid.UUID]:
    if val is None or isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except (ValueError, AttributeError):
        return None


@router.post("/request", response_model=ApprovalResponse, status_code=status.HTTP_201_CREATED, summary="Create approval request")
async def create_approval_request(
    data: ApprovalCreate,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Request human approval for a privileged/dangerous agent action."""
    approval = ApprovalRequest(
        id=uuid4(),
        task_id=data.task_id or uuid4(),
        requested_by_user_id=current_user.id,
        action=data.action_type or "privileged_action",
        reason=data.reasoning or data.action_description or "No reason provided",
        risk_level=data.potential_impact or "medium",
        status="pending",
        requested_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )

    db_session.add(approval)
    await db_session.commit()
    await db_session.refresh(approval)

    return approval.to_dict()


@router.get("/pending", response_model=List[ApprovalResponse], summary="List pending approvals")
async def list_pending_approvals(
    limit: int = 50,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """List all pending approval requests."""
    result = await db_session.execute(
        select(ApprovalRequest)
        .where(ApprovalRequest.status == "pending")
        .where(ApprovalRequest.expires_at > datetime.now(timezone.utc))
        .order_by(ApprovalRequest.requested_at.desc())
        .limit(limit)
    )
    approvals = result.scalars().all()
    return [approval.to_dict() for approval in approvals]


@router.get("/history", response_model=List[ApprovalResponse], summary="List approval history")
async def list_approval_history(
    task_id: Optional[str] = None,
    limit: int = 100,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """List approval history for audit."""
    query = select(ApprovalRequest).order_by(ApprovalRequest.requested_at.desc()).limit(limit)

    if task_id:
        t_uuid = to_uuid(task_id)
        if t_uuid:
            query = query.where(ApprovalRequest.task_id == t_uuid)

    result = await db_session.execute(query)
    approvals = result.scalars().all()
    return [approval.to_dict() for approval in approvals]


@router.post("/{approval_id}/approve", response_model=ApprovalResponse, summary="Approve request")
async def approve_request(
    approval_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Approve an approval request."""
    a_uuid = to_uuid(approval_id)
    if not a_uuid:
        raise HTTPException(status_code=404, detail="Approval request not found")

    result = await db_session.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == a_uuid)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")

    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="Approval request is not pending")

    if approval.is_expired:
        raise HTTPException(status_code=410, detail="Approval request has expired")

    approval.status = "approved"
    approval.approved_by_user_id = current_user.id
    approval.approved_at = datetime.now(timezone.utc)
    approval.outcome = f"Approved by {current_user.username or current_user.email}"

    await db_session.commit()
    await db_session.refresh(approval)

    return approval.to_dict()


@router.post("/{approval_id}/reject", response_model=ApprovalResponse, summary="Reject request")
async def reject_request(
    approval_id: str,
    data: Optional[dict] = None,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Reject an approval request."""
    a_uuid = to_uuid(approval_id)
    if not a_uuid:
        raise HTTPException(status_code=404, detail="Approval request not found")

    result = await db_session.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == a_uuid)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")

    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="Approval request is not pending")

    approval.status = "rejected"
    approval.rejection_reason = (data or {}).get("reason", "Rejected by user")
    approval.outcome = f"Rejected by {current_user.username or current_user.email}"

    await db_session.commit()
    await db_session.refresh(approval)

    return approval.to_dict()


@router.post("/{approval_id}/cancel", response_model=ApprovalResponse, summary="Cancel request")
async def cancel_request(
    approval_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Cancel an approval request."""
    a_uuid = to_uuid(approval_id)
    if not a_uuid:
        raise HTTPException(status_code=404, detail="Approval request not found")

    result = await db_session.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == a_uuid)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")

    if approval.status not in ["pending", "reviewing"]:
        raise HTTPException(status_code=400, detail="Can only cancel pending/reviewing approvals")

    approval.status = "cancelled"
    approval.outcome = f"Cancelled by {current_user.username or current_user.email}"

    await db_session.commit()
    await db_session.refresh(approval)

    return approval.to_dict()


@router.get("/{approval_id}", response_model=ApprovalResponse, summary="Get approval details")
async def get_approval(
    approval_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get full details of an approval request."""
    a_uuid = to_uuid(approval_id)
    if not a_uuid:
        raise HTTPException(status_code=404, detail="Approval request not found")

    result = await db_session.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == a_uuid)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")

    return approval.to_dict()


@router.get("/my-pending", response_model=List[ApprovalResponse], summary="List my pending approvals")
async def list_my_pending(
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """List approvals requested by the current user."""
    result = await db_session.execute(
        select(ApprovalRequest).where(
            and_(
                ApprovalRequest.requested_by_user_id == current_user.id,
                ApprovalRequest.status == "pending"
            )
        ).order_by(ApprovalRequest.requested_at.desc())
    )
    approvals = result.scalars().all()
    return [approval.to_dict() for approval in approvals]
