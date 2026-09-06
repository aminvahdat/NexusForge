import asyncio
import structlog
from datetime import datetime
from typing import Optional, Dict, Any

from app.db import get_db_session
from app.models.task import Task, TaskStatus
from app.execution.state import ExecutionState, ExecutionStatus
from app.execution.events import Event, EventType
from app.execution.lifecycle import ExecutionLifecycle

logger = structlog.get_logger()


class ExecutionMonitor:
    """Real-time execution tracking service using existing Redis/DB infrastructure."""

    def __init__(self):
        self.active_executions: Dict[str, ExecutionState] = {}

    async def start_execution(
        self,
        task_id: str,
        worker_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        state, event = ExecutionLifecycle.create_execution(
            execution_id=execution_id,
            task_id=task_id,
        )
        self.active_executions[execution_id] = state
        logger.info(
            "execution.created",
            execution_id=execution_id,
            task_id=task_id,
            event_type=event.event_type.name,
        )
        return {"execution_id": execution_id, "status": state.status.value, "event": event.to_dict()}

    async def update_execution_status(
        self,
        execution_id: str,
        status: ExecutionStatus,
        message: Optional[str] = None,
    ) -> Optional[Event]:
        state = self.active_executions.get(execution_id)
        if not state:
            return None
        event = ExecutionLifecycle.transition(
            state, status, message or status.value
        )
        return event

    async def complete(
        self,
        execution_id: str,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        state = self.active_executions.get(execution_id)
        if not state:
            return None
        if error:
            event = ExecutionLifecycle.fail_execution(state, error)
            logger.info("execution.failed", execution_id=execution_id, error=error)
        else:
            event = ExecutionLifecycle.complete_execution(state, result)
            logger.info("execution.completed", execution_id=execution_id, result=result)
        return {
            "execution_id": execution_id,
            "status": state.status.value,
            "event": event.to_dict(),
        }


monitor = ExecutionMonitor()