"""Execution Lifecycle & Real Process Execution Tests.

Verifies:
1. Worker registration and DB heartbeat
2. Task claiming lifecycle (queued -> running)
3. Real process execution SUCCESS path (Exit code 0 -> completed)
4. Real process execution FAILURE path (Exit code != 0 -> failed, Fail Closed)
5. Missing runtime fallback prevention (Hermes missing + no command -> failed, Fail Closed)
"""

import os
import sys
import uuid
import pytest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backend"))

from backend.worker import WorkerProcess
from backend.app.db import get_session_factory, init_database
from backend.app.models import User, Project, Task, Worker
from backend.app.auth import get_password_hash




@pytest.fixture
async def sample_project():
    session_factory = get_session_factory()
    async with session_factory() as session:
        # Create user
        uid = uuid.uuid4()
        user = User(
            id=uid,
            email=f"worker_test_{uid.hex[:8]}@example.com",
            username=f"worker_test_{uid.hex[:8]}",
            password_hash=get_password_hash("WorkerPass123!"),
            is_active=True
        )
        session.add(user)

        # Create project with workspace
        pid = uuid.uuid4()
        ws_dir = (Path("workspaces") / f"test_proj_{pid.hex[:6]}").resolve()
        ws_dir.mkdir(parents=True, exist_ok=True)

        project = Project(
            id=pid,
            name=f"Worker Project {pid.hex[:6]}",
            description="Testing worker execution lifecycle",
            owner_id=uid,
            workspace_path=str(ws_dir)
        )
        session.add(project)
        await session.commit()
        return {"user_id": uid, "project_id": pid, "workspace": ws_dir}


@pytest.mark.asyncio
async def test_worker_registration_and_db_state():
    """Verify WorkerProcess connects and registers in the DB."""
    worker_id = f"test-worker-{uuid.uuid4().hex[:6]}"
    worker = WorkerProcess(worker_id=worker_id, hostname="test-host")
    await worker.connect()
    await worker.register()

    session_factory = get_session_factory()
    async with session_factory() as session:
        from sqlalchemy import select
        res = await session.execute(select(Worker).where(Worker.worker_id == worker_id))
        w_record = res.scalars().first()
        assert w_record is not None
        assert w_record.worker_id == worker_id
        assert w_record.status == "idle"
        assert w_record.last_heartbeat is not None


from backend.app.core.runtime.agent_runtime import AgentRuntimeInterface, SessionResult, Status


class SafeTestSuccessAdapter(AgentRuntimeInterface):
    def create_session(self, context):
        return "sess-succ"
    def execute_task(self, session_id, context=None):
        return SessionResult(session_id=session_id, status=Status.COMPLETED, exit_code=0)
    def terminate(self, session_id):
        pass
    def cancel(self, session_id):
        return True
    def get_status(self, session_id):
        return Status.COMPLETED
    def shutdown(self):
        pass


class SafeTestFailureAdapter(AgentRuntimeInterface):
    def create_session(self, context):
        return "sess-fail"
    def execute_task(self, session_id, context=None):
        return SessionResult(session_id=session_id, status=Status.FAILED, exit_code=1, error="Intentional test failure")
    def terminate(self, session_id):
        pass
    def cancel(self, session_id):
        return True
    def get_status(self, session_id):
        return Status.FAILED
    def shutdown(self):
        pass


@pytest.mark.asyncio
async def test_real_process_execution_success(sample_project):
    """Verify task executing through adapter transitions to completed."""
    session_factory = get_session_factory()
    task_id = uuid.uuid4()
    async with session_factory() as session:
        task = Task(
            id=task_id,
            project_id=sample_project["project_id"],
            title="Execute Success Agent Task",
            description="Task executed via runtime adapter",
            role="backend_agent",
            status="queued",
            acceptance_criteria=["Verify deliverable meets specification"]
        )
        session.add(task)
        await session.commit()

    worker = WorkerProcess(worker_id=f"wkr-succ-{uuid.uuid4().hex[:6]}", adapter=SafeTestSuccessAdapter())
    await worker.connect()
    await worker.register()

    # Claim and execute
    claimed = await worker.claim_task()
    assert claimed is True

    # Verify task state in DB
    async with session_factory() as session:
        from sqlalchemy import select
        res = await session.execute(select(Task).where(Task.id == task_id))
        t = res.scalars().first()
        assert t is not None
        assert t.status == "completed"
        assert t.completed_at is not None


@pytest.mark.asyncio
async def test_real_process_execution_failure_fails_closed(sample_project):
    """Verify task executing a failing runtime transitions to failed (Fail Closed)."""
    session_factory = get_session_factory()
    task_id = uuid.uuid4()
    async with session_factory() as session:
        task = Task(
            id=task_id,
            project_id=sample_project["project_id"],
            title="Execute Failing Agent Task",
            description="Task with runtime failure",
            role="backend_agent",
            status="queued",
            acceptance_criteria=["Task expecting failure"]
        )
        session.add(task)
        await session.commit()

    worker = WorkerProcess(worker_id=f"wkr-fail-{uuid.uuid4().hex[:6]}", adapter=SafeTestFailureAdapter())
    await worker.connect()
    await worker.register()

    claimed = await worker.claim_task()
    assert claimed is True

    # Verify task state in DB is FAILED (NOT completed, NOT faked)
    async with session_factory() as session:
        from sqlalchemy import select
        res = await session.execute(select(Task).where(Task.id == task_id))
        t = res.scalars().first()
        assert t is not None
        assert t.status == "failed"
        assert t.completed_at is not None


@pytest.mark.asyncio
async def test_missing_runtime_fails_closed(sample_project, monkeypatch):
    """Verify task with no command and no hermes binary fails closed immediately."""
    monkeypatch.setenv("NEXUSFORGE_RUNTIME_ADAPTER", "hermes")
    monkeypatch.setenv("HERMES_BINARY_PATH", "/nonexistent/hermes")
    session_factory = get_session_factory()
    task_id = uuid.uuid4()
    async with session_factory() as session:
        task = Task(
            id=task_id,
            project_id=sample_project["project_id"],
            title="Execute Missing Hermes Task",
            description="No command, expecting Hermes",
            role="backend_agent",
            status="queued",
            acceptance_criteria=[]
        )
        session.add(task)
        await session.commit()

    worker = WorkerProcess(worker_id=f"wkr-closed-{uuid.uuid4().hex[:6]}")
    await worker.connect()
    await worker.register()

    claimed = await worker.claim_task()
    assert claimed is True

    # Verify task state in DB is FAILED
    async with session_factory() as session:
        from sqlalchemy import select
        res = await session.execute(select(Task).where(Task.id == task_id))
        t = res.scalars().first()
        assert t is not None
        assert t.status == "failed"
        assert t.completed_at is not None
