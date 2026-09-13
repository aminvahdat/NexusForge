import asyncio
import os
import signal
import subprocess
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import structlog

from app.db import get_db_session
from app.models import Task
from app.models.enums import TaskStatus
from app.execution.state import ExecutionState, ExecutionStatus
from app.execution.events import Event, EventType
from app.execution.lifecycle import ExecutionLifecycle

logger = structlog.get_logger()



class ExecutionMonitor:
    """Real-time execution tracking service using existing Redis/DB infrastructure."""

    def __init__(self):
        self.active_executions: Dict[str, ExecutionState] = {}
        self.running_processes: Dict[str, Dict[str, Any]] = {}

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

    def register_process(
        self,
        execution_id: str,
        pid: int,
        worker_id: str,
        workspace: str,
        start_time: Optional[datetime] = None,
        proc: Any = None,
    ) -> None:
        """Track running process metadata for process control (cancel, timeout, retire)."""
        self.running_processes[execution_id] = {
            "execution_id": execution_id,
            "pid": pid,
            "worker_id": worker_id,
            "workspace": workspace,
            "start_time": start_time or datetime.now(timezone.utc),
            "proc": proc,
        }
        logger.info("process.registered", execution_id=execution_id, pid=pid, worker_id=worker_id)

    def unregister_process(self, execution_id: str) -> None:
        """Remove process from tracking after completion or termination."""
        self.running_processes.pop(execution_id, None)

    def get_process_info(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve recorded process info for execution."""
        return self.running_processes.get(execution_id)

    def terminate_process(self, execution_id: str) -> bool:
        """Terminate the actual running process and any child processes (process tree)."""
        info = self.running_processes.get(execution_id)
        if not info:
            logger.warning("process.terminate_not_found", execution_id=execution_id)
            return False

        pid = info.get("pid")
        proc = info.get("proc")
        killed = False

        # If asyncio subprocess handle exists, kill it directly
        if proc:
            try:
                proc.kill()
                killed = True
            except Exception as e:
                logger.warning("process.kill_handle_failed", execution_id=execution_id, error=str(e))

        # Ensure entire process tree is terminated via OS primitives
        if pid:
            try:
                if os.name == "nt":
                    # Windows: /F = forcefully, /T = tree (all children)
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(pid)],
                        capture_output=True,
                        check=False,
                    )
                    killed = True
                else:
                    # POSIX: terminate process group or process
                    try:
                        os.killpg(os.getpgid(pid), signal.SIGKILL)
                    except (AttributeError, ProcessLookupError, PermissionError):
                        os.kill(pid, signal.SIGKILL)
                    killed = True
            except Exception as e:
                logger.warning("process.tree_kill_failed", execution_id=execution_id, pid=pid, error=str(e))

        self.unregister_process(execution_id)
        logger.info("process.terminated", execution_id=execution_id, pid=pid, success=killed)
        return killed

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
        self.unregister_process(execution_id)
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