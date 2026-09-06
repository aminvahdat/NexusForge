"""API routes for NexusForge execution monitoring and real-time event delivery."""

import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Set, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db_session
from app.models.task import Task
from app.models import Project
from app.schemas.task import TaskResponse
from app.schemas.project import ProjectResponse
from app.services.execution_monitor import monitor
from app.services.worker import WorkerPool

router = APIRouter(prefix="/execution", tags=["execution", "realtime"])
logger = logging.getLogger(__name__)

# Connection tracking for cleanup
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, client_id: str = None):
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_metadata[websocket] = {
            "client_id": client_id,
            "connected_at": datetime.now(timezone.utc),
            "last_ping": datetime.now(timezone.utc),
            "subscriptions": set(),
        }
        logger.info(f"WebSocket client connected: {client_id or 'unknown'} ({len(self.active_connections)} total)")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        self.connection_metadata.pop(websocket, None)
        logger.info(f"WebSocket client disconnected ({len(self.active_connections)} total)")

    def update_ping(self, websocket: WebSocket):
        if websocket in self.connection_metadata:
            self.connection_metadata[websocket]["last_ping"] = datetime.now(timezone.utc)

    def add_subscription(self, websocket: WebSocket, event_type: str):
        if websocket in self.connection_metadata:
            self.connection_metadata[websocket]["subscriptions"].add(event_type)

    def remove_subscription(self, websocket: WebSocket, event_type: str):
        if websocket in self.connection_metadata:
            self.connection_metadata[websocket]["subscriptions"].discard(event_type)

    def get_client_connections(self, client_id: str) -> Set[WebSocket]:
        return {
            ws for ws, meta in self.connection_metadata.items()
            if meta.get("client_id") == client_id
        }

    async def broadcast_to_subscribers(self, event_type: str, data: dict):
        """Broadcast event only to clients subscribed to this event type"""
        disconnected = set()
        for websocket in self.active_connections.copy():
            try:
                meta = self.connection_metadata.get(websocket, {})
                subscriptions = meta.get("subscriptions", set())
                if not subscriptions or event_type in subscriptions:
                    await websocket.send_json(data)
            except Exception as e:
                logger.warning(f"Failed to send to websocket: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected clients
        for ws in disconnected:
            self.disconnect(ws)

connection_manager = ConnectionManager()


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


@router.post("/{execution_id}/pause", response_model=dict, summary="Pause execution")
async def pause_execution(
    execution_id: str,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Pause an active execution."""
    # Get execution state
    state = monitor.active_executions.get(execution_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    
    if state.status != "running":
        raise HTTPException(status_code=400, detail=f"Execution {execution_id} is not running")
    
    # Update execution state
    state.status = "paused"
    state.paused_at = datetime.now(timezone.utc)
    
    # Update task status
    task_result = await db_session.execute(select(Task).where(Task.id == state.task_id))
    task = task_result.scalar_one_or_none()
    if task:
        task.status = "paused"
        task.updated_at = datetime.now(timezone.utc)
        await db_session.commit()
    
    # Emit execution.paused event
    event = await monitor.update_execution_status(
        execution_id, "paused", f"Execution {execution_id} paused by user request"
    )
    
    return {
        "execution_id": execution_id,
        "status": "paused",
        "message": f"Execution {execution_id} paused",
        "paused_at": state.paused_at.isoformat()
    }


@router.post("/{execution_id}/resume", response_model=dict, summary="Resume execution")
async def resume_execution(
    execution_id: str,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Resume a paused execution."""
    # Get execution state
    state = monitor.active_executions.get(execution_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    
    if state.status != "paused":
        raise HTTPException(status_code=400, detail=f"Execution {execution_id} is not paused")
    
    # Update execution state
    state.status = "running"
    state.resumed_at = datetime.now(timezone.utc)
    
    # Update task status
    task_result = await db_session.execute(select(Task).where(Task.id == state.task_id))
    task = task_result.scalar_one_or_none()
    if task:
        task.status = "running"
        task.updated_at = datetime.now(timezone.utc)
        await db_session.commit()
    
    # Emit execution.resumed event
    event = await monitor.update_execution_status(
        execution_id, "resumed", f"Execution {execution_id} resumed by user request"
    )
    
    return {
        "execution_id": execution_id,
        "status": "running",
        "message": f"Execution {execution_id} resumed",
        "resumed_at": state.resumed_at.isoformat()
    }


@router.post("/{execution_id}/retire", response_model=dict, summary="Retire execution")
async def retire_execution(
    execution_id: str,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Retire (cancel) an execution."""
    # Get execution state
    state = monitor.active_executions.get(execution_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    
    # Update execution state
    state.status = "retired"
    state.retired_at = datetime.now(timezone.utc)
    
    # Update task status
    task_result = await db_session.execute(select(Task).where(Task.id == state.task_id))
    task = task_result.scalar_one_or_none()
    if task:
        task.status = "retired"
        task.updated_at = datetime.now(timezone.utc)
        await db_session.commit()
    
    # Emit execution.retired event
    event = await monitor.update_execution_status(
        execution_id, "retired", f"Execution {execution_id} retired by user request"
    )
    
    return {
        "execution_id": execution_id,
        "status": "retired",
        "message": f"Execution {execution_id} retired",
        "retired_at": state.retired_at.isoformat()
    }


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


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time execution updates.
    
    Phase 5.5 Hardening:
    - ConnectionManager tracks all active connections
    - Graceful disconnect handling
    - Malformed message validation
    - Connection metadata (subscriptions, ping)
    - Auto-cleanup on disconnect
    """
    await connection_manager.connect(websocket, client_id)
    logger.info(f"WebSocket connection established for client: {client_id}")
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            
            # Validate JSON
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                logger.warning(f"Malformed JSON from client {client_id}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON message"
                })
                continue
            
            # Handle message types
            msg_type = message.get("type", "")
            
            if msg_type == "ping":
                connection_manager.update_ping(websocket)
                await websocket.send_json({"type": "pong"})
                
            elif msg_type == "subscribe":
                event_types = message.get("event_types", [])
                for et in event_types:
                    connection_manager.add_subscription(websocket, et)
                logger.debug(f"Client {client_id} subscribed: {event_types}")
                
            elif msg_type == "unsubscribe":
                event_types = message.get("event_types", [])
                for et in event_types:
                    connection_manager.remove_subscription(websocket, et)
                    
            elif msg_type == "execution_subscribe":
                execution_id = message.get("execution_id")
                if execution_id:
                    connection_manager.add_subscription(websocket, f"execution:{execution_id}")
                    
            elif msg_type == "execution_unsubscribe":
                execution_id = message.get("execution_id")
                if execution_id:
                    connection_manager.remove_subscription(websocket, f"execution:{execution_id}")
                    
            else:
                logger.warning(f"Unknown message type from {client_id}: {msg_type}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}"
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket client {client_id} disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
    finally:
        connection_manager.disconnect(websocket)
        logger.info(f"WebSocket cleanup complete for client: {client_id}")


@router.get("/health", response_model=dict, summary="WebSocket and execution health check")
async def websocket_health():
    """Returns current WebSocket connection statistics for monitoring."""
    return {
        "status": "ok",
        "active_connections": len(connection_manager.active_connections),
        "active_executions": len(monitor.active_executions),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }