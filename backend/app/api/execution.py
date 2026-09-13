"""API routes for NexusForge execution monitoring and real-time event delivery."""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Set, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from jose import JWTError, jwt
from app.db import get_db_session
from app.models import Task, Project, User
from app.schemas.task import TaskResponse
from app.schemas.project import ProjectResponse
from app.services.execution_monitor import monitor
from app.auth import get_current_user, SECRET_KEY, ALGORITHM
from app.authorization import enforce_ownership


def to_uuid(val: Any) -> uuid.UUID:
    if isinstance(val, uuid.UUID):
        return val
    return uuid.UUID(str(val))


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
    current_user: User = Depends(get_current_user),
):
    """Start execution of a task and return execution ID."""
    from app.services.database import get_task, get_project
    task = await get_task(db_session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    if task.project_id:
        project = await get_project(db_session, str(task.project_id))
        if project:
            enforce_ownership(project.owner_id, current_user, "task")

    execution_result = await monitor.start_execution(task_id=task_id)

    task.status = "running"
    task.started_at = datetime.now(timezone.utc)
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
    current_user: User = Depends(get_current_user),
):
    """Mark execution as complete or failed."""
    event = await monitor.complete(execution_id, result, error)
    if not event:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

    task_id = event["execution_id"]
    result_data = event["event"]
    task_status = "completed" if not error else "failed"

    task_result = await db_session.execute(select(Task).where(Task.id == task_id))
    task = task_result.scalar_one_or_none()
    if task:
        task.status = task_status
        task.completed_at = datetime.now(timezone.utc)
        task.updated_at = datetime.now(timezone.utc)
        db_session.add(task)
        await db_session.commit()

    return result_data


@router.post("/{execution_id}/pause", response_model=dict, summary="Pause execution")
async def pause_execution(
    execution_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Pause an active execution with ownership verification."""
    state = monitor.active_executions.get(execution_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    
    # Phase 12: Authorized Execution Control
    task_result = await db_session.execute(select(Task).where(Task.id == to_uuid(state.task_id)))
    task = task_result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task associated with execution not found")
    if task.project_id:
        proj_res = await db_session.execute(select(Project).where(Project.id == task.project_id))
        project = proj_res.scalar_one_or_none()
        if project:
            enforce_ownership(project.owner_id, current_user, "execution")

    # Phase 11: Real Process Control - Windows does not support SIGSTOP/SIGCONT process pausing
    import os
    if os.name == "nt":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Process pause is not supported on this platform: Windows does not support native SIGSTOP/SIGCONT process freezing."
        )

    if state.status != "running":
        raise HTTPException(status_code=400, detail=f"Execution {execution_id} is not running")

    # Send SIGSTOP on POSIX
    import signal
    proc_info = monitor.get_process_info(execution_id)
    if proc_info and proc_info.get("pid"):
        try:
            os.kill(proc_info["pid"], signal.SIGSTOP)
        except Exception as e:
            logger.warning(f"sigstop_failed for pid {proc_info['pid']}: {e}")

    state.status = "paused"
    state.paused_at = datetime.now(timezone.utc)
    task.status = "paused"
    task.updated_at = datetime.now(timezone.utc)
    await db_session.commit()
    
    await monitor.update_execution_status(
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
    current_user: User = Depends(get_current_user),
):
    """Resume a paused execution with ownership verification."""
    state = monitor.active_executions.get(execution_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    
    # Phase 12: Authorized Execution Control
    task_result = await db_session.execute(select(Task).where(Task.id == to_uuid(state.task_id)))
    task = task_result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task associated with execution not found")
    if task.project_id:
        proj_res = await db_session.execute(select(Project).where(Project.id == task.project_id))
        project = proj_res.scalar_one_or_none()
        if project:
            enforce_ownership(project.owner_id, current_user, "execution")

    import os
    if os.name == "nt":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Process resume is not supported on this platform: Windows does not support native SIGSTOP/SIGCONT process freezing."
        )

    if state.status != "paused":
        raise HTTPException(status_code=400, detail=f"Execution {execution_id} is not paused")

    # Send SIGCONT on POSIX
    import signal
    proc_info = monitor.get_process_info(execution_id)
    if proc_info and proc_info.get("pid"):
        try:
            os.kill(proc_info["pid"], signal.SIGCONT)
        except Exception as e:
            logger.warning(f"sigcont_failed for pid {proc_info['pid']}: {e}")

    state.status = "running"
    state.resumed_at = datetime.now(timezone.utc)
    task.status = "running"
    task.updated_at = datetime.now(timezone.utc)
    await db_session.commit()
    
    await monitor.update_execution_status(
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
    current_user: User = Depends(get_current_user),
):
    """Retire (cancel) an execution with real process termination and worker state reset."""
    state = monitor.active_executions.get(execution_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    
    # Phase 12: Authorized Execution Control
    task_result = await db_session.execute(select(Task).where(Task.id == to_uuid(state.task_id)))
    task = task_result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task associated with execution not found")
    if task.project_id:
        proj_res = await db_session.execute(select(Project).where(Project.id == task.project_id))
        project = proj_res.scalar_one_or_none()
        if project:
            enforce_ownership(project.owner_id, current_user, "execution")

    # Phase 11: Real Process Control - Terminate actual running process tree
    monitor.terminate_process(execution_id)

    state.status = "retired"
    state.retired_at = datetime.now(timezone.utc)
    
    task.status = "cancelled"
    task.updated_at = datetime.now(timezone.utc)
    
    # Reset assigned worker state to idle
    from app.models import Worker
    from sqlalchemy import update
    if state.worker_id:
        await db_session.execute(
            update(Worker)
            .where(Worker.worker_id == state.worker_id)
            .values(status="idle", current_task_id=None, current_task_count=0)
        )

    await db_session.commit()
    
    await monitor.update_execution_status(
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
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get current status of an execution with ownership enforcement."""
    state = monitor.active_executions.get(execution_id)
    if not state:
        return {"execution_id": execution_id, "status": "not_found"}

    task_result = await db_session.execute(select(Task).where(Task.id == to_uuid(state.task_id)))
    task = task_result.scalar_one_or_none()
    if task and task.project_id:
        proj_res = await db_session.execute(select(Project).where(Project.id == task.project_id))
        project = proj_res.scalar_one_or_none()
        if project:
            enforce_ownership(project.owner_id, current_user, "execution")

    return {
        "execution_id": execution_id,
        "status": state.status.value if hasattr(state.status, "value") else str(state.status),
        "task_id": state.task_id,
        "worker_id": state.worker_id,
    }


@router.get("/list", response_model=dict, summary="List active executions")
async def list_executions(
    current_user: User = Depends(get_current_user),
):
    """List all active (in-memory) executions."""
    executions = {}
    for eid, state in monitor.active_executions.items():
        executions[eid] = {
            "status": state.status.value if hasattr(state.status, "value") else str(state.status),
            "task_id": state.task_id,
            "worker_id": state.worker_id,
            "events": len(state.events),
        }
    return {"active_executions": executions, "count": len(monitor.active_executions)}


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, token: Optional[str] = None):
    """WebSocket endpoint for real-time execution updates with JWT authentication and ownership checks."""
    # Verify token before connection
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required")
        return

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token payload")
            return
    except JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or expired token")
        return

    await connection_manager.connect(websocket, client_id)
    connection_manager.connection_metadata[websocket]["user_id"] = str(sub)
    logger.info(f"WebSocket connection established for client: {client_id} (sub: {sub})")
    
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
                    # Phase 13: Verify user ownership of the requested execution resource
                    user_id = connection_manager.connection_metadata.get(websocket, {}).get("user_id")
                    authorized = False
                    try:
                        from app.db import get_session_factory
                        sf = get_session_factory()
                        async with sf() as session:
                            st = monitor.active_executions.get(execution_id)
                            if st:
                                t_res = await session.execute(select(Task).where(Task.id == to_uuid(st.task_id)))
                                t = t_res.scalar_one_or_none()
                                if t and t.project_id:
                                    p_res = await session.execute(select(Project).where(Project.id == t.project_id))
                                    p = p_res.scalar_one_or_none()
                                    if p and (str(p.owner_id) == str(user_id) or not p.owner_id):
                                        authorized = True
                    except Exception as ex:
                        logger.warning(f"Error checking WS ownership: {ex}")

                    if authorized:
                        connection_manager.add_subscription(websocket, f"execution:{execution_id}")
                        await websocket.send_json({
                            "type": "subscribed",
                            "resource": f"execution:{execution_id}"
                        })
                    else:
                        logger.warning(f"Unauthorized WS subscription attempt for {execution_id} by user {user_id}")
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Unauthorized: access to execution {execution_id} forbidden"
                        })
                    
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