"""Worker control & telemetry API routes for active worker management."""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.db import get_db_session
from app.models import Worker, Task, User
from app.auth import get_current_user
from app.schemas.worker import WorkerControlResponse

router = APIRouter(tags=["worker", "controls"])


@router.get("/workers")
async def get_workers_telemetry(
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Return telemetry, health, load, and assigned tasks for real active worker nodes."""
    completed_count = (await db_session.execute(
        select(func.count(Task.id)).where(Task.status == "completed")
    )).scalar() or 0

    running_count = (await db_session.execute(
        select(func.count(Task.id)).where(Task.status == "running")
    )).scalar() or 0

    queued_count = (await db_session.execute(
        select(func.count(Task.id)).where(Task.status.in_(["queued", "planning", "ready"]))
    )).scalar() or 0

    failed_count = (await db_session.execute(
        select(func.count(Task.id)).where(Task.status == "failed")
    )).scalar() or 0

    # Query real worker records from DB
    result = await db_session.execute(select(Worker).order_by(Worker.created_at.desc()))
    db_workers = result.scalars().all()

    workers_list = []
    for w in db_workers:
        # If worker is running a task, fetch task title
        task_title = None
        if w.current_task_id:
            task_res = await db_session.execute(
                select(Task.title).where(Task.id == w.current_task_id)
            )
            task_title = task_res.scalar_one_or_none()

        workers_list.append({
            "id": str(w.id),
            "worker_id": w.worker_id,
            "hostname": w.hostname or "unknown",
            "name": w.worker_id,
            "status": w.status,
            "current_task_id": str(w.current_task_id) if w.current_task_id else None,
            "current_task_title": task_title,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_queued": queued_count,
            "tasks_running": 1 if w.status == "busy" else 0,
            "cpu_usage": 0.0,
            "memory_usage": "N/A",
            "uptime": "N/A",
            "last_heartbeat": w.last_heartbeat.isoformat() if w.last_heartbeat else None,
            "started_at": w.created_at.isoformat() if w.created_at else None,
            "meta_info": {
                "concurrency": w.max_concurrent_tasks or 1,
                "engine": "NexusForge Execution Engine",
                "assigned_agents": w.skills or []
            },
            "execution_events": []
        })

    active_count = len([w for w in workers_list if w["status"] not in ("offline", "retired")])

    return {
        "workers": workers_list,
        "count": len(workers_list),
        "total_active": active_count,
        "queue_stats": {
            "queued": queued_count,
            "running": running_count,
            "completed": completed_count,
            "failed": failed_count
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/workers/{worker_id}")
async def get_worker_detail(
    worker_id: str,
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Get details of a specific worker node by worker_id or UUID."""
    query = select(Worker).where(Worker.worker_id == worker_id)
    try:
        w_uuid = uuid.UUID(worker_id)
        query = select(Worker).where(or_(Worker.worker_id == worker_id, Worker.id == w_uuid))
    except (ValueError, AttributeError):
        pass

    result = await db_session.execute(query)
    worker = result.scalars().first()
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker '{worker_id}' not found"
        )

    # Fetch assigned tasks
    tasks_res = await db_session.execute(
        select(Task).where(Task.assigned_worker_id == worker.id).order_by(Task.updated_at.desc()).limit(10)
    )
    assigned_tasks = [t.to_dict() for t in tasks_res.scalars().all()]

    return {
        "id": str(worker.id),
        "worker_id": worker.worker_id,
        "hostname": worker.hostname,
        "status": worker.status,
        "current_task_id": str(worker.current_task_id) if worker.current_task_id else None,
        "role": worker.role,
        "skills": worker.skills or [],
        "last_heartbeat": worker.last_heartbeat.isoformat() if worker.last_heartbeat else None,
        "created_at": worker.created_at.isoformat() if worker.created_at else None,
        "tasks": assigned_tasks,
    }


# Worker controls
@router.post("/worker-controls/pause/{worker_id}", response_model=WorkerControlResponse)
@router.post("/workers/pause/{worker_id}", response_model=WorkerControlResponse)
async def pause_worker(
    worker_id: str,
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    query = select(Worker).where(Worker.worker_id == worker_id)
    try:
        w_uuid = uuid.UUID(worker_id)
        query = select(Worker).where(or_(Worker.worker_id == worker_id, Worker.id == w_uuid))
    except (ValueError, AttributeError):
        pass

    result = await db_session.execute(query)
    worker = result.scalars().first()
    if worker:
        worker.status = "paused"
        await db_session.commit()

    return {"worker_id": worker_id, "action": "pause", "status": "paused"}


@router.post("/worker-controls/resume/{worker_id}", response_model=WorkerControlResponse)
@router.post("/workers/resume/{worker_id}", response_model=WorkerControlResponse)
async def resume_worker(
    worker_id: str,
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    query = select(Worker).where(Worker.worker_id == worker_id)
    try:
        w_uuid = uuid.UUID(worker_id)
        query = select(Worker).where(or_(Worker.worker_id == worker_id, Worker.id == w_uuid))
    except (ValueError, AttributeError):
        pass

    result = await db_session.execute(query)
    worker = result.scalars().first()
    if worker:
        worker.status = "idle"
        await db_session.commit()

    return {"worker_id": worker_id, "action": "resume", "status": "active"}


@router.post("/worker-controls/retire/{worker_id}", response_model=WorkerControlResponse)
@router.post("/workers/retire/{worker_id}", response_model=WorkerControlResponse)
async def retire_worker(
    worker_id: str,
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
    query = select(Worker).where(Worker.worker_id == worker_id)
    try:
        w_uuid = uuid.UUID(worker_id)
        query = select(Worker).where(or_(Worker.worker_id == worker_id, Worker.id == w_uuid))
    except (ValueError, AttributeError):
        pass

    result = await db_session.execute(query)
    worker = result.scalars().first()
    if worker:
        worker.status = "retired"
        await db_session.commit()

    return {"worker_id": worker_id, "action": "retire", "status": "retired"}
