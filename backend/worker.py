#!/usr/bin/env python3
import asyncio
import argparse
import logging
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import structlog
from sqlalchemy import text

from app.config.settings import get_settings
from app.models.enums import AgentRole as DBAgentRole, TaskStatus
from app.db import get_engine, get_session_factory
from app.services.redis import get_redis
from app.services.execution_monitor import monitor
from app.execution.events import EventType
from app.core.runtime.agent_runtime import HermesRuntimeAdapter, ExecutionContext, Status

# Configure structlog (sync)
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger()


class WorkerProcess:
    def __init__(self, worker_id: str = None, hostname: str = None):
        self.worker_id = worker_id or f"wkr-{os.getpid()}"
        self.hostname = hostname or os.uname().nodename
        self.adapter: HermesRuntimeAdapter = None
        self.running = False
        self.heartbeat_task = None
        self._engine = None
        self._session_factory = None

    async def _get_engine(self):
        if self._engine is None:
            self._engine = get_engine()
        return self._engine

    async def _get_session_factory(self):
        if self._session_factory is None:
            self._session_factory = get_session_factory()
        return self._session_factory

    async def connect(self) -> None:
        """Connect to PostgreSQL and Redis."""
        logger.info("worker_connecting", worker_id=self.worker_id)

        # PostgreSQL: test connection by getting a session and running SELECT 1
        try:
            engine = await self._get_engine()
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT 1 AS result"))
                row = result.scalar()
                if row == 1:
                    logger.info("db_connect_success", worker_id=self.worker_id)
                else:
                    raise RuntimeError(f"Unexpected SELECT 1 result: {row}")
        except Exception as exc:
            logger.error("db_connect_failed", worker_id=self.worker_id, error=str(exc))
            raise RuntimeError(f"Database connection failed: {exc}") from exc

        # Redis
        try:
            redis = await get_redis()
            ping = await redis.ping()
            logger.info("redis_connect_success", worker_id=self.worker_id, ping=ping)
        except Exception as exc:
            logger.error("redis_connect_failed", worker_id=self.worker_id, error=str(exc))
            raise RuntimeError(f"Redis connection failed: {exc}") from exc

    async def register(self) -> None:
        """Register worker with Redis state."""
        logger.info("worker_registering", worker_id=self.worker_id, hostname=self.hostname)
        try:
            redis = await get_redis()
            await redis.hset("WORKER_STATE", self.worker_id, "idle")
            logger.info("worker_registered_redis", worker_id=self.worker_id)
        except Exception as exc:
            logger.error("worker_register_redis_failed", worker_id=self.worker_id, error=str(exc))

    async def heartbeat(self) -> None:
        """Send periodic heartbeat to Redis (every 5 seconds)."""
        while self.running:
            try:
                redis = await get_redis()
                await redis.hset("WORKER_STATE", self.worker_id, "idle")
                await redis.expire("WORKER_STATE", 30)
                logger.info("worker_heartbeat", worker_id=self.worker_id, status="idle")
            except Exception as exc:
                logger.error("heartbeat_failed", worker_id=self.worker_id, error=str(exc))
            await asyncio.sleep(5)

    async def claim_task(self) -> bool:
        """Claim an assigned task from DB and execute it."""
        try:
            session_factory = await self._get_session_factory()
            async with session_factory() as session:
                # Find queued task not yet assigned
                from sqlalchemy import select
                from app.models import Task
                from app.models.enums import TaskStatus as DBTaskStatus

                result = await session.execute(
                    select(Task).where(Task.status == DBTaskStatus.QUEUED.value).limit(1)
                )
                task = result.scalar_one_or_none()

                if not task:
                    logger.info("no_queued_task", worker_id=self.worker_id)
                    return False

                # Create execution record in ExecutionMonitor
                execution_result = await monitor.start_execution(
                    task_id=str(task.id),
                    worker_id=self.worker_id,
                )
                execution_id = execution_result["execution_id"]
                logger.info("execution_created", execution_id=execution_id, task_id=str(task.id))

                # Claim it
                task.status = TaskStatus.RUNNING
                task.assigned_worker = self.worker_id
                task.started_at = datetime.now(timezone.utc)
                await session.commit()
                logger.info("task_claimed", task_id=str(task.id), worker_id=self.worker_id)

                # Emit execution.started event
                event = await monitor.update_execution_status(
                    execution_id, "started", f"Execution started by worker {self.worker_id}"
                )
                if event:
                    logger.info("execution_started_event", execution_id=execution_id, event_type=event.event_type.name)

                # Execute
                await self.execute_task(session, task, execution_id)
                return True

        except Exception as exc:
            logger.error("claim_task_failed", worker_id=self.worker_id, error=str(exc))
            return False

    async def execute_task(self, session, task, execution_id: str) -> None:
        """Execute task via Hermes runtime."""
        try:
            # Load role (map DB role name to adapter role)
            role = self._map_role(task.role or "generalist")

            # Adapter (Hermes binary check)
            if self.adapter is None:
                self.adapter = HermesRuntimeAdapter(timeout=180)
                try:
                    self.adapter.initialize()
                    logger.info("hermes_initialized", worker_id=self.worker_id)
                except RuntimeError as exc:
                    logger.error("hermes_init_failed", worker_id=self.worker_id, error=str(exc), _run_fallback=True)
                    task.status = TaskStatus.FAILED
                    task.error_message = f"Hermes init failed: {exc}"
                    task.completed_at = datetime.now(timezone.utc)
                    await session.commit()
                    # Emit execution.failed event
                    await monitor.complete(execution_id, error=str(exc))
                    return

            # Workspace
            workspace = f"/workspaces/{task.project_id or 'global'}"
            Path(workspace).mkdir(parents=True, exist_ok=True)

            # Execution context
            context = ExecutionContext(
                project_id=str(task.project_id) if task.project_id else None,
                task_id=str(task.id),
                role=role,
                workspace_path=workspace,
                allowed_tools=["terminal", "coding", "file", "project", "skills"],
                approval_policy="smart",
                max_execution_time=180,
            )

            # Hermes session + execution
            session_id = self.adapter.create_session(context)
            logger.info("hermes_session_created", session_id=session_id, worker_id=self.worker_id)

            result = self.adapter.execute_task(session_id, context)

            # Update task
            task.status = TaskStatus.COMPLETED if result.status == Status.COMPLETED else TaskStatus.FAILED
            task.completed_at = datetime.now(timezone.utc)
            task.execution_result = result.output
            task.artifacts = result.artifacts
            task.duration_seconds = result.execution_duration_sec
            task.error_message = result.error if result.status == Status.FAILED else None

            await session.commit()
            logger.info(
                "task_execution_done",
                task_id=str(task.id),
                status=task.status.value,
                duration=result.execution_duration_sec,
            )

            # Emit execution completed/failed event
            if task.status == TaskStatus.COMPLETED:
                await monitor.complete(execution_id, result=result.output)
                logger.info("execution_completed_event", execution_id=execution_id)
            else:
                error_msg = task.error_message or "Unknown error"
                await monitor.complete(execution_id, error=error_msg)
                logger.info("execution_failed_event", execution_id=execution_id, error=error_msg)

            self.adapter.terminate(session_id)

        except Exception as exc:
            logger.error("task_execution_failed", task_id=str(task.id), error=str(exc))
            task.status = TaskStatus.FAILED
            task.error_message = str(exc)
            task.completed_at = datetime.now(timezone.utc)
            await session.commit()

            # Emit execution.failed event
            await monitor.complete(execution_id, error=str(exc))

    def _map_role(self, role_str: str) -> DBAgentRole:
        """Map DB role name to adapter AgentRole (hardcoded in agent_runtime)."""
        mapping = {
            "chief_orchestrator": DBAgentRole.CHIEF_ORCHESTRATOR,
            "project_planner": DBAgentRole.PROJECT_PLANNER,
            "software_architect": DBAgentRole.SOFTWARE_ARCHITECT,
            "research_agent": DBAgentRole.RESEARCH_AGENT,
            "ui_ux_agent": DBAgentRole.UI_UX_AGENT,
            "frontend_agent": DBAgentRole.FRONTEND_AGENT,
            "backend_agent": DBAgentRole.BACKEND_AGENT,
            "mobile_agent": DBAgentRole.MOBILE_AGENT,
            "database_agent": DBAgentRole.DATABASE_AGENT,
            "security_agent": DBAgentRole.SECURITY_AGENT,
            "qa_agent": DBAgentRole.QA_AGENT,
            "devops_agent": DBAgentRole.DEVOPS_AGENT,
            "chief": DBAgentRole.CHIEF_ORCHESTRATOR,
            "researcher": DBAgentRole.RESEARCH_AGENT,
            "architect": DBAgentRole.SOFTWARE_ARCHITECT,
            "backend_engineer": DBAgentRole.BACKEND_AGENT,
            "frontend_engineer": DBAgentRole.FRONTEND_AGENT,
            "generalist": DBAgentRole.CHIEF_ORCHESTRATOR,
        }
        lower = role_str.lower()
        return mapping.get(lower, DBAgentRole.CHIEF_ORCHESTRATOR)

    async def run_loop(self) -> None:
        """Main worker loop."""
        try:
            await self.connect()
            await self.register()

            self.heartbeat_task = asyncio.create_task(self.heartbeat())
            logger.info("worker_started", worker_id=self.worker_id, hostname=self.hostname)

            while self.running:
                claimed = await self.claim_task()
                if not claimed:
                    await asyncio.sleep(2)

        except asyncio.CancelledError:
            logger.info("worker_cancelled", worker_id=self.worker_id)
        except Exception as exc:
            logger.error("worker_fatal_error", worker_id=self.worker_id, error=str(exc))
        finally:
            self.running = False
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    pass
            # Cleanup engines
            if self._engine:
                # Note: we don't have a direct way to dispose the engine from get_engine() without globals
                # For simplicity, we rely on process exit to cleanup.
                pass
            logger.info("worker_shutdown", worker_id=self.worker_id)

    async def stop(self) -> None:
        """Stop worker gracefully."""
        logger.info("worker_stop_requested", worker_id=self.worker_id)
        self.running = False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker-id")
    parser.add_argument("--hostname")
    args = parser.parse_args()

    worker = WorkerProcess(worker_id=args.worker_id, hostname=args.hostname)
    worker.running = True

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def shutdown(signum, frame):
        loop.create_task(worker.stop())

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    try:
        loop.run_until_complete(worker.run_loop())
    except KeyboardInterrupt:
        logger.info("worker_keyboard_interrupt", worker_id=worker.worker_id)
    except Exception as exc:
        logger.error("worker_fatal_error", error=str(exc))
        sys.exit(1)
    finally:
        loop.close()


if __name__ == "__main__":
    main()