"""API routes for NexusForge execution monitoring and real-time event delivery."""

import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db_session
from app.models.task import Task
from app.models import Project
from app.schemas.task import TaskResponse
from app.schemas.project import ProjectResponse
from app.services.execution_monitor import monitor
from app.services.worker import workers

router = APIRouter(prefix="/execution", tags=["execution", "realtime"])


@router.post("/start/{task_id}", response_model=dict, summary="Start a task execution")
async def start_execution(
    task_id: str,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Start execution of a task and return execution ID."""
    # Verify task exists
    result = await db_session.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # Start execution
    execution_result = await monitor.start_execution(task_id=task_id)

    # Mark task as running
    task.status = "running"
    task.updated_at = datetime.now(timezone.utc)
    db_session.add(task)
    await db_session.commit()

    return execution_result


@router.post("/{execution_id}/complete", response_model=dict, summary="Complete execution")
async def complete_execution(
    execution_id: str,
    result: Optional[str] = None,
    error: Optional[str] = None,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Mark execution as complete or failed."""
    event = await monitor.complete(execution_id, result, error)
    if not event:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

    # Update task status based on execution result
    task_id = event["execution_id"]
    result_data = event["event"]
    task_status = TaskStatus.COMPLETED if not error else TaskStatus.FAILED

    task_result = await db_session.execute(select(Task).where(Task.id == task_id))
    task = task_result.scalar_one_or_none()
    if task:
        task.status = task_status
        task.updated_at = datetime.now(timezone.utc)
        if error:
            task.error = error
        db_session.add(task)
        await db_session.commit()

    return result_data


@router.get("/status/{execution_id}", response_model=dict, summary="Get execution status")
async def execution_status(
    execution_id: str,
):
    """Get current status of an execution."""
    result = monitor.active_executions.get(execution_id)
    if not result:
        return {"execution_id": execution_id, "status": "not_found"}
    return {"execution_id": execution_id, "status": result["status"], "event": result["event"]}


@router.get("/list", response_model=dict, summary="List active executions")
async def list_executions():
    """List all active (in-memory) executions."""
    executions = {}
    for eid, state in monitor.active_executions.items():
        executions[eid] = {
            "status": state.status.value,
            "task_id": state.task_id,
            "worker_id": state.worker_id,
            "events": len(state.events),
        }
    return {"active_executions": executions, "count": len(monitor.active_executions)}