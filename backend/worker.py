#!/usr/bin/env python3
"""NexusForge Worker Process.

Real, fail-closed worker process for task execution:
- Connects to database and Redis (with graceful offline fallback).
- Registers itself in the DB `workers` table and updates heartbeats.
- Atomically claims queued tasks.
- Executes real processes (Hermes CLI or validated command scripts).
- Fails closed on missing runtimes or non-zero exit codes.
- Zero mock pipelines, zero fake sleeps, zero fabricated scores.
"""

import asyncio
import argparse
import logging
import os
import shlex
import signal
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import structlog
from sqlalchemy import select, text, update

from app.config.settings import get_settings
from app.models.enums import TaskStatus
from app.models import Task, Worker, Project, Artifact
from app.db import get_engine, get_session_factory
from app.services.redis import get_redis
from app.services.execution_monitor import monitor
from app.core.runtime.agent_runtime import HermesRuntimeAdapter, ExecutionContext, Status

# Configure structlog
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
    _claim_lock = asyncio.Lock()  # Class-level lock for in-process coroutine concurrency (SQLite)

    def __init__(self, worker_id: Optional[str] = None, hostname: Optional[str] = None, adapter: Optional[Any] = None):
        self.hostname = hostname or (hasattr(os, "uname") and os.uname().nodename) or socket.gethostname()
        self.worker_id = worker_id or f"wkr-{self.hostname}-{os.getpid()}"
        self.adapter = adapter
        self.running = False
        self.heartbeat_task: Optional[asyncio.Task] = None
        self._engine = None
        self._session_factory = None
        self._redis = None
        self.db_worker_id = None

    async def _get_engine(self):
        if self._engine is None:
            self._engine = get_engine()
        return self._engine

    async def _get_session_factory(self):
        if self._session_factory is None:
            self._session_factory = get_session_factory()
        return self._session_factory

    async def connect(self) -> None:
        """Connect to Database and Redis."""
        logger.info("worker_connecting", worker_id=self.worker_id)

        # Database connection check
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

        # Redis connection (graceful fallback)
        try:
            self._redis = await get_redis()
            if self._redis:
                await self._redis.ping()
                logger.info("redis_connect_success", worker_id=self.worker_id)
            else:
                logger.warning("redis_offline_mode", worker_id=self.worker_id)
        except Exception as exc:
            logger.warning("redis_connect_failed_graceful_fallback", worker_id=self.worker_id, error=str(exc))
            self._redis = None

    async def register(self) -> None:
        """Register worker in DB `workers` table and Redis."""
        logger.info("worker_registering", worker_id=self.worker_id, hostname=self.hostname)
        now = datetime.now(timezone.utc)

        # Register in DB
        try:
            session_factory = await self._get_session_factory()
            async with session_factory() as session:
                res = await session.execute(select(Worker).where(Worker.worker_id == self.worker_id))
                worker_record = res.scalars().first()
                if worker_record:
                    worker_record.status = "idle"
                    worker_record.hostname = self.hostname
                    worker_record.last_heartbeat = now
                    self.db_worker_id = worker_record.id
                else:
                    new_worker = Worker(
                        worker_id=self.worker_id,
                        hostname=self.hostname,
                        status="idle",
                        created_at=now,
                        last_heartbeat=now,
                        max_concurrent_tasks=1,
                        current_task_count=0,
                        skills=["generalist"]
                    )
                    session.add(new_worker)
                    await session.flush()
                    self.db_worker_id = new_worker.id

                await session.commit()
                logger.info("worker_registered_db", worker_id=self.worker_id, db_id=str(self.db_worker_id))
        except Exception as exc:
            logger.error("worker_register_db_failed", worker_id=self.worker_id, error=str(exc))
            raise

        # Register in Redis if connected
        if self._redis:
            try:
                await self._redis.hset("WORKER_STATE", self.worker_id, "idle")
                logger.info("worker_registered_redis", worker_id=self.worker_id)
            except Exception as exc:
                logger.warning("worker_register_redis_failed", error=str(exc))

    async def heartbeat(self) -> None:
        """Send periodic heartbeat to DB and Redis every 5 seconds."""
        while self.running:
            now = datetime.now(timezone.utc)
            curr_status = "idle"
            try:
                session_factory = await self._get_session_factory()
                async with session_factory() as session:
                    res = await session.execute(
                        select(Worker.status).where(Worker.worker_id == self.worker_id)
                    )
                    curr_status = res.scalar_one_or_none() or "idle"
                    await session.execute(
                        update(Worker)
                        .where(Worker.worker_id == self.worker_id)
                        .values(last_heartbeat=now)
                    )
                    await session.commit()
            except Exception as exc:
                logger.warning("heartbeat_db_failed", worker_id=self.worker_id, error=str(exc))

            if self._redis:
                try:
                    await self._redis.hset("WORKER_STATE", self.worker_id, curr_status)
                    await self._redis.expire("WORKER_STATE", 30)
                except Exception:
                    pass

            await asyncio.sleep(5)

    async def claim_task(self) -> bool:
        """Claim an assigned task from DB and execute it with atomic claiming and concurrency control."""
        try:
            settings = get_settings()
            max_concurrent = getattr(settings, "max_concurrent_workers", 2)

            session_factory = await self._get_session_factory()
            engine = await self._get_engine()
            is_pg = engine.dialect.name == "postgresql"

            task = None
            execution_id = None

            # Serialize claiming to guarantee atomic reservation
            async with WorkerProcess._claim_lock:
                async with session_factory() as session:
                    # 1. Check worker status: if paused or retired, do not claim tasks
                    w_res = await session.execute(
                        select(Worker.status).where(Worker.worker_id == self.worker_id)
                    )
                    worker_status = w_res.scalar_one_or_none()
                    if worker_status == "paused":
                        logger.info("worker_paused_skipping_claim", worker_id=self.worker_id)
                        return False
                    elif worker_status == "retired":
                        logger.info("worker_retired_stopping", worker_id=self.worker_id)
                        self.running = False
                        return False

                    # 2. Acquire transaction-level advisory lock on PostgreSQL to prevent races across containers
                    if is_pg:
                        await session.execute(text("SELECT pg_advisory_xact_lock(74839201)"))

                    # 3. Concurrency Limit Enforcement (Atomic under lock)
                    active_res = await session.execute(
                        select(Task.id).where(Task.status == "running")
                    )
                    running_tasks = active_res.scalars().all()
                    if len(running_tasks) >= max_concurrent:
                        logger.info("concurrency_limit_reached", running=len(running_tasks), limit=max_concurrent)
                        if is_pg:
                            await session.rollback()
                        return False

                    # 4. Atomic Task Claiming
                    if is_pg:
                        claim_query = (
                            select(Task)
                            .where(Task.status.in_(["queued", "planning", "ready"]))
                            .order_by(Task.created_at.asc())
                            .with_for_update(skip_locked=True)
                            .limit(1)
                        )
                        res = await session.execute(claim_query)
                        candidate = res.scalar_one_or_none()
                        if not candidate:
                            await session.rollback()
                            return False
                        task_id = candidate.id
                    else:
                        res = await session.execute(
                            select(Task.id)
                            .where(Task.status.in_(["queued", "planning", "ready"]))
                            .order_by(Task.created_at.asc())
                            .limit(1)
                        )
                        task_id = res.scalar_one_or_none()
                        if not task_id:
                            return False

                    now = datetime.now(timezone.utc)
                    # Atomic conditional transition: state must still be queued/planning/ready
                    claim_stmt = (
                        update(Task)
                        .where(Task.id == task_id, Task.status.in_(["queued", "planning", "ready"]))
                        .values(status="running", started_at=now, assigned_worker_id=self.db_worker_id)
                    )
                    update_res = await session.execute(claim_stmt)
                    if update_res.rowcount == 0:
                        # Race condition prevented: task already claimed by another worker
                        await session.rollback()
                        logger.info("claim_race_prevented", task_id=str(task_id), worker_id=self.worker_id)
                        return False

                    # Update worker status to busy
                    await session.execute(
                        update(Worker)
                        .where(Worker.worker_id == self.worker_id)
                        .values(status="busy", current_task_id=task_id, current_task_count=1)
                    )
                    await session.commit()

                    # Re-fetch claimed task instance
                    claimed_res = await session.execute(select(Task).where(Task.id == task_id))
                    task = claimed_res.scalar_one()

                    logger.info("task_claimed", task_id=str(task.id), worker_id=self.worker_id)

                    # Create execution record in ExecutionMonitor
                    execution_result = await monitor.start_execution(
                        task_id=str(task.id),
                        worker_id=self.worker_id,
                    )
                    execution_id = execution_result["execution_id"]

                    # Emit execution.started event
                    await monitor.update_execution_status(
                        execution_id, "started", f"Execution started by worker {self.worker_id}"
                    )

            # Execute task outside the claim lock so other workers can utilize remaining concurrency slots
            async with session_factory() as session:
                await self.execute_task(session, task, execution_id)
                return True

        except Exception as exc:
            logger.error("claim_task_failed", worker_id=self.worker_id, error=str(exc))
            return False

    async def execute_task(self, session, task: Task, execution_id: str) -> None:
        """Execute task via AgentRuntimeInterface (Option A: User command execution permanently removed)."""
        logger.info("executing_task", task_id=str(task.id), title=task.title)
        now = datetime.now(timezone.utc)

        # Setup workspace
        workspace_dir = Path("workspaces") / str(task.project_id)
        if task.project_id:
            proj_res = await session.execute(select(Project).where(Project.id == task.project_id))
            project = proj_res.scalars().first()
            if project and project.workspace_path:
                workspace_dir = Path(project.workspace_path)

        workspace_dir = workspace_dir.resolve()
        workspace_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Determine configured Agent Runtime Adapter
            runtime_available = False
            if self.adapter is None:
                adapter_mode = os.getenv("AGENT_RUNTIME_ADAPTER", "hermes").lower()
                if adapter_mode == "hermes":
                    self.adapter = HermesRuntimeAdapter(timeout=180)
                    try:
                        self.adapter.initialize()
                        runtime_available = True
                    except Exception as exc:
                        logger.warning("hermes_runtime_init_failed", error=str(exc))
                        runtime_available = False
                else:
                    runtime_available = False
            else:
                runtime_available = True

            if runtime_available and self.adapter:
                # Execute via configured Agent Runtime Adapter
                logger.info("executing_agent_runtime", task_id=str(task.id), adapter=self.adapter.__class__.__name__)
                await monitor.update_execution_status(execution_id, "running", f"Executing via {self.adapter.__class__.__name__}")

                # Register task & execution in Redis for distributed tracking and cancellation
                if self._redis:
                    try:
                        await self._redis.set(f"nexusforge:exec_to_task:{execution_id}", str(task.id), ex=3600)
                        await self._redis.set(f"nexusforge:task_to_exec:{task.id}", execution_id, ex=3600)
                    except Exception:
                        pass

                ctx = ExecutionContext(
                    project_id=str(task.project_id) if task.project_id else None,
                    task_id=str(task.id),
                    workspace_path=str(workspace_dir),
                    task_prompt=f"{task.title} {task.description or ''}"
                )

                sess_id = self.adapter.create_session(ctx) if hasattr(self.adapter, "create_session") else "default"

                # Run execution in background thread so worker can monitor cancellation concurrently
                exec_future = asyncio.to_thread(self.adapter.execute_task, sess_id, ctx)
                exec_task = asyncio.create_task(exec_future)

                # Give child process a moment to spawn and register genuine OS PID
                await asyncio.sleep(0.1)
                proc = getattr(self.adapter, "get_process", lambda s: None)(sess_id)
                if proc and proc.pid:
                    monitor.register_process(
                        execution_id=execution_id,
                        pid=proc.pid,
                        worker_id=self.worker_id,
                        workspace=str(workspace_dir),
                        proc=proc
                    )

                # Active cancellation and timeout watcher loop
                is_cancelled = False
                while not exec_task.done():
                    # Check Redis cancellation signal
                    if self._redis:
                        try:
                            cancel_req = await self._redis.get(f"nexusforge:cancel:{execution_id}")
                            if cancel_req:
                                is_cancelled = True
                                break
                        except Exception:
                            pass

                    # Check DB task status
                    session_factory = await self._get_session_factory()
                    async with session_factory() as check_session:
                        res = await check_session.execute(select(Task.status).where(Task.id == task.id))
                        cur_status = res.scalar_one_or_none()
                        if cur_status in ("cancelled", "retired"):
                            is_cancelled = True
                            break

                    await asyncio.sleep(0.5)

                if is_cancelled:
                    logger.info("execution_cancelled", task_id=str(task.id), execution_id=execution_id)
                    # Terminate process tree immediately
                    if hasattr(self.adapter, "cancel"):
                        self.adapter.cancel(sess_id)
                    monitor.terminate_process(execution_id)
                    exec_task.cancel()

                    cancelled_now = datetime.now(timezone.utc)
                    await session.execute(
                        update(Task)
                        .where(Task.id == task.id)
                        .values(status="cancelled", completed_at=cancelled_now)
                    )
                    task.status = "cancelled"
                    task.completed_at = cancelled_now
                    await session.commit()
                    await monitor.complete(execution_id, error="Execution cancelled by user")
                    return

                # Normal execution completion
                result = await exec_task
                exit_code = getattr(result, "exit_code", 0)
                error_msg = getattr(result, "error", None)

                if exit_code == 0:
                    completed_now = datetime.now(timezone.utc)
                    await session.execute(
                        update(Task)
                        .where(Task.id == task.id)
                        .values(status="completed", completed_at=completed_now)
                    )
                    task.status = "completed"
                    task.completed_at = completed_now

                    # Scan workspace for generated artifacts
                    if workspace_dir.exists():
                        for f in workspace_dir.iterdir():
                            if f.is_file() and not f.name.startswith("."):
                                art = Artifact(
                                    project_id=task.project_id,
                                    task_id=task.id,
                                    name=f.name,
                                    type="code",
                                    description=f"Deliverable {f.name}",
                                    path=str(f),
                                    size=f.stat().st_size,
                                    mime_type="text/plain",
                                    version="1.0"
                                )
                                session.add(art)

                    await session.commit()
                    await monitor.complete(execution_id)
                else:
                    failed_now = datetime.now(timezone.utc)
                    await session.execute(
                        update(Task)
                        .where(Task.id == task.id)
                        .values(status="failed", completed_at=failed_now)
                    )
                    task.status = "failed"
                    task.completed_at = failed_now
                    await session.commit()
                    await monitor.complete(execution_id, error=f"Runtime failed with code {exit_code}: {error_msg}")

            else:
                # FAIL CLOSED: Runtime unavailable and user command execution is forbidden
                fail_reason = (
                    "Execution failed closed: Agent runtime is unavailable, "
                    "and arbitrary host command execution is prohibited for security."
                )
                logger.error("execution_fail_closed", task_id=str(task.id), reason=fail_reason)
                fail_now = datetime.now(timezone.utc)
                await session.execute(
                    update(Task)
                    .where(Task.id == task.id)
                    .values(status="failed", completed_at=fail_now)
                )
                task.status = "failed"
                task.completed_at = fail_now
                await session.commit()
                await monitor.complete(execution_id, error=fail_reason)

        except Exception as exc:
            logger.error("task_execution_exception", task_id=str(task.id), error=str(exc))
            fail_now = datetime.now(timezone.utc)
            task.status = "failed"
            task.completed_at = fail_now
            try:
                await session.execute(
                    update(Task)
                    .where(Task.id == task.id)
                    .values(status="failed", completed_at=fail_now)
                )
                await session.commit()
            except Exception:
                pass
            await monitor.complete(execution_id, error=str(exc))

        finally:
            # Return worker to idle state unless paused or retired
            try:
                session_factory = await self._get_session_factory()
                async with session_factory() as fin_session:
                    w_curr = await fin_session.execute(select(Worker.status).where(Worker.worker_id == self.worker_id))
                    st = w_curr.scalar_one_or_none()
                    target_status = "idle" if st not in ("paused", "retired") else st
                    await fin_session.execute(
                        update(Worker)
                        .where(Worker.worker_id == self.worker_id)
                        .values(status=target_status, current_task_id=None, current_task_count=0)
                    )
                    await fin_session.commit()
            except Exception:
                pass

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

            # Mark worker offline in DB
            try:
                session_factory = await self._get_session_factory()
                async with session_factory() as session:
                    await session.execute(
                        update(Worker)
                        .where(Worker.worker_id == self.worker_id)
                        .values(status="offline", current_task_id=None, current_task_count=0)
                    )
                    await session.commit()
            except Exception:
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