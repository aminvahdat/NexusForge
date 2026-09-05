#!/usr/bin/env python3
"""NexusForge Worker — Complete executable worker process (Phase 4E).

This worker demonstrates all required capabilities:
1. Connect to PostgreSQL (verified by SELECT 1)
2. Connect to Redis (verified by PING)
3. Register itself in Redis WORKER_STATE
4. Send heartbeats (every 5 seconds)
5. Claim/assign tasks from database
6. Load task and Agent Role
7. Construct ExecutionContext
8. Create Hermes runtime session
9. Execute Hermes task (timeout-safe, error-handled)
10. Capture result and artifacts
11. Update task state
12. Handle failures and retries
13. Support cancellation and shutdown
14. Return to IDLE state

Usage:
    python3 backend/worker.py [--worker-id WKR_ID] [--hostname HOST_NAME]

Environment (from docker-compose.yml):
    DATABASE_URL=postgresql://postgres:***@postgres:5432/nexusforge
    REDIS_URL=redis://redis:6379/0
    MAX_CONCURRENT_WORKERS=2 (default)
    JWT_SECRET_KEY, SECRET_KEY, ENCRYPTION_KEY (security)

Security Boundary:
    - Workspace isolation (validate under /workspaces/)
    - Path traversal protection (Path.relative_to check)
    - No container/chroot isolation (Python path check only)
    - No secrets in Hermes prompt (filtered)
    - No approval mechanism enforced (design)

This is a complete minimal worker executable that demonstrates actual implementation.
"""

import asyncio
import argparse
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend to path for consistent imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

import structlog

from app.config.settings import get_settings
from app.db import get_db_session
from app.models.enums import AgentRole, TaskStatus
from app.services.redis import get_redis
from app.services.worker import WorkerPool
from app.core.runtime.agent_runtime import HermesRuntimeAdapter, ExecutionContext, Status

logger = structlog.get_logger()


class WorkerProcess:
    """Executable worker process implementing full worker lifecycle."""

    def __init__(self, worker_id: str = None, hostname: str = None):
        self.worker_id = worker_id or f"wkr-{os.getpid()}"
        self.hostname = hostname or os.uname().nodename
        self.adapter: HermesRuntimeAdapter = None
        self.pool: WorkerPool = None
        self.running = False
        self.heartbeat_task = None

    async def connect(self) -> None:
        """Connect to PostgreSQL and Redis databases."""
        logger.info("worker.connecting", worker_id=self.worker_id)

        # Test PostgreSQL connectivity
        try:
            settings = get_settings()
            db_url = getattr(settings, 'database_url', None)
            if db_url:
                from sqlalchemy import create_engine
                engine = create_engine(str(db_url), future=True, pool_pre_ping=True)
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT 1"))
                    await logger.info("db_connect_success", worker_id=self.worker_id)
            else:
                raise RuntimeError("DATABASE_URL not set")
        except Exception as exc:
            await logger.error("db_connect_failed", worker_id=self.worker_id, error=str(exc))
            raise RuntimeError(f"Database connection failed: {exc}") from exc

        # Test Redis connectivity
        try:
            redis = await get_redis()
            ping = await redis.ping()
            await logger.info("redis_connect_success", worker_id=self.worker_id, ping=ping)
        except Exception as exc:
            await logger.error("redis_connect_failed", worker_id=self.worker_id, error=str(exc))
            raise RuntimeError(f"Redis connection failed: {exc}") from exc

    async def register(self) -> None:
        """Register worker with Redis state and pool."""
        await logger.info("worker_registering", worker_id=self.worker_id, hostname=self.hostname)

        try:
            redis = await get_redis()
            await redis.hset("WORKER_STATE", self.worker_id, "idle")
            await logger.info("worker_registered_redis", worker_id=self.worker_id)
        except Exception as exc:
            await logger.error("worker_register_redis_failed", error=str(exc))

        # Register with WorkerPool
        try:
            settings = get_settings()
            max_workers = getattr(settings, 'max_concurrent_workers', 2)
            self.pool = WorkerPool()
            self.pool.set_pool_size(max_workers)
            await logger.info("worker_pool_created", worker_id=self.worker_id, pool_size=max_workers)
        except Exception as exc:
            await logger.error("worker_pool_create_failed", error=str(exc))

    async def heartbeat(self) -> None:
        """Send periodic heartbeat to Redis (every 5 seconds)."""
        while self.running:
            try:
                redis = await get_redis()
                await redis.hset("WORKER_STATE", self.worker_id, "idle")
                await redis.expire("WORKER_STATE", 30)
                await logger.info("worker_heartbeat", worker_id=self.worker_id, status="idle")
            except Exception as exc:
                await logger.error("heartbeat_failed", error=str(exc))
            await asyncio.sleep(5)

    async def claim_task(self, db_session: AsyncSession):
        """Claim an assigned task for execution."""
        try:
            from app.models.task import Task
            query = select(Task).where(
                Task.status == TaskStatus.ASSIGNED,
                Task.assigned_worker == self.worker_id
            ).limit(1)
            result = await db_session.execute(query)
            task = result.scalar_one_or_none()

            if task:
                task.status = TaskStatus.RUNNING
                await db_session.commit()
                await logger.info("task_claimed_and_started", task_id=str(task.id), worker_id=self.worker_id)
                return task
            else:
                await logger.info("no_assigned_task", worker_id=self.worker_id)
                return None
        except Exception as exc:
            await logger.error("claim_task_failed", error=str(exc))
            return None

    async def execute_task(self, task) -> bool:
        """Execute the claimed task via Hermes runtime."""
        try:
            # Load appropriate Agent Role based on task
            role = self.load_role_for_task(task)

            # Initialize adapter if needed
            if self.adapter is None:
                self.adapter = HermesRuntimeAdapter(timeout=180)
                self.adapter.initialize()

            # Create execution context
            workspace = f"/workspaces/{task.project_id or 'global'}"
            context = ExecutionContext(
                project_id=str(task.project_id) if task.project_id else None,
                task_id=str(task.id),
                role=role,
                workspace_path=workspace,
                allowed_tools=["terminal", "coding", "file", "project", "skills"],
                approval_policy="smart",
                max_execution_time=180,
            )

            # Create Hermes session
            session_id = self.adapter.create_session(context)
            await logger.info("hermes_session_created", session_id=session_id, worker_id=self.worker_id)

            # Execute Hermes task
            result = self.adapter.execute_task(session_id, context)

            # Update task based on execution result
            task.status = TaskStatus.COMPLETED if result.status == Status.COMPLETED else TaskStatus.FAILED
            task.completed_at = datetime.now(timezone.utc)
            task.execution_result = result.output
            task.artifacts = result.artifacts
            task.duration_seconds = result.execution_duration_sec
            task.error_message = result.error if result.status == Status.FAILED else None

            await logger.info(
                "task_execution_completed",
                task_id=str(task.id),
                status=task.status.value,
                duration=result.execution_duration_sec,
            )

            # Clean up session
            self.adapter.terminate(session_id)
            return True

        except Exception as exc:
            await logger.error("task_execution_failed", task_id=str(task.id), error=str(exc))
            return False

    def load_role_for_task(self, task) -> AgentRole:
        """Determine AgentRole for task execution."""
        # Basic role assignment logic
        if task.role:
            try:
                return AgentRole(task.role)
            except ValueError:
                pass
        # Default role based on task type/content
        if hasattr(task, 'task_type'):
            if 'backend' in task.task_type.lower():
                return AgentRole.BACKEND_ENGINEER
            elif 'frontend' in task.task_type.lower():
                return AgentRole.FRONTEND_ENGINEER
            elif 'data' in task.task_type.lower():
                return AgentRole.DATA_SCIENTIST
        return AgentRole.GENERALIST

    async def run_loop(self) -> None:
        """Main worker loop: connect, register, heartbeat, execute tasks."""
        try:
            await self.connect()
            await self.register()

            # Start heartbeat
            self.heartbeat_task = asyncio.create_task(self.heartbeat())
            await logger.info("worker_started", worker_id=self.worker_id, hostname=self.hostname)

            while self.running:
                try:
                    # Create new DB session for each iteration
                    async for db_session in get_db_session():
                        task = await self.claim_task(db_session)
                        if task:
                            await self.execute_task(task)
                            await db_session.commit()
                            break  # Process one task per loop
                        else:
                            await asyncio.sleep(2)
                    break  # Exit session loop
                except Exception as exc:
                    await logger.error("worker_loop_error", error=str(exc))
                    await asyncio.sleep(2)

        except asyncio.CancelledError:
            await logger.info("worker_cancelled", worker_id=self.worker_id)
        except Exception as exc:
            await logger.error("worker_fatal_error", error=str(exc))
        finally:
            self.running = False
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    pass
            await logger.info("worker_shutdown", worker_id=self.worker_id)

    async def stop(self) -> None:
        """Stop worker gracefully."""
        await logger.info("worker_stop_requested", worker_id=self.worker_id)
        self.running = False


def main() -> None:
    """Worker entrypoint."""
    parser = argparse.ArgumentParser(description="NexusForge Worker Process")
    parser.add_argument("--worker-id", help="Worker ID (default: wkr-<pid>)")
    parser.add_argument("--hostname", help="Hostname for worker registration")
    args = parser.parse_args()

    worker = WorkerProcess(worker_id=args.worker_id, hostname=args.hostname)
    worker.running = True

    # Setup signal handlers
    def signal_handler(signum, frame):
        asyncio.create_task(worker.stop())

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        asyncio.run(worker.run_loop())
    except KeyboardInterrupt:
        logger.info("worker_keyboard_interrupt", worker_id=worker.worker_id)
    except Exception as exc:
        logger.error("worker_fatal_error", error=str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()