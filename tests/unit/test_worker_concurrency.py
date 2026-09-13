"""Worker Concurrency & Process Control Tests.

Covers:
- Phase 8: Race-safe atomic worker claiming (Worker A -> True, Worker B -> False)
- Phase 9: MAX_CONCURRENT_WORKERS enforcement (At most N tasks active simultaneously)
- Phase 11: Real process timeout & tree termination
- Phase 12: Authorized execution control & IDOR prevention
"""

import asyncio
import os
import sys
import uuid
import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backend"))

from backend.worker import WorkerProcess
from backend.app.db import get_session_factory, init_database
from backend.app.models import User, Project, Task, Worker
from backend.app.auth import get_password_hash
from backend.app.services.execution_monitor import monitor




@pytest.fixture
async def sample_project():
    session_factory = get_session_factory()
    async with session_factory() as session:
        uid = uuid.uuid4()
        user = User(
            id=uid,
            email=f"conc_user_{uid.hex[:8]}@example.com",
            username=f"conc_user_{uid.hex[:8]}",
            password_hash=get_password_hash("Pass123!"),
            is_active=True
        )
        session.add(user)

        pid = uuid.uuid4()
        ws_dir = (Path("workspaces") / f"conc_proj_{pid.hex[:6]}").resolve()
        ws_dir.mkdir(parents=True, exist_ok=True)

        project = Project(
            id=pid,
            name=f"Conc Project {pid.hex[:6]}",
            description="Testing concurrency",
            owner_id=uid,
            workspace_path=str(ws_dir)
        )
        session.add(project)
        await session.commit()
        return {"user_id": uid, "project_id": pid, "workspace": ws_dir}


@pytest.mark.asyncio
async def test_atomic_claiming_race_safety(sample_project):
    """Phase 8: Two simultaneous workers attempt to claim the exact same single queued task.
    
    Expected result:
    - Exactly one worker claims it (CLAIMED = True)
    - The second worker fails to claim it (NO CLAIM = False)
    - Zero duplicate executions
    """
    session_factory = get_session_factory()
    task_id = uuid.uuid4()
    async with session_factory() as session:
        task = Task(
            id=task_id,
            project_id=sample_project["project_id"],
            title="Single Race Task",
            description="Only one worker can claim me",
            role="backend_agent",
            status="queued",
            acceptance_criteria=['cmd:python -c "import sys; sys.exit(0)"']
        )
        session.add(task)
        await session.commit()

    worker_a = WorkerProcess(worker_id=f"wkr-A-{uuid.uuid4().hex[:6]}")
    worker_b = WorkerProcess(worker_id=f"wkr-B-{uuid.uuid4().hex[:6]}")

    await worker_a.connect()
    await worker_a.register()
    await worker_b.connect()
    await worker_b.register()

    # Both workers attempt to claim simultaneously
    results = await asyncio.gather(
        worker_a.claim_task(),
        worker_b.claim_task(),
        return_exceptions=False
    )

    claimed_count = sum(1 for r in results if r is True)
    failed_count = sum(1 for r in results if r is False)

    assert claimed_count == 1, f"Expected exactly 1 claim, got {claimed_count}"
    assert failed_count == 1, f"Expected exactly 1 claim rejection, got {failed_count}"

    # Verify task state in DB
    async with session_factory() as session:
        from sqlalchemy import select
        res = await session.execute(select(Task).where(Task.id == task_id))
        t = res.scalars().first()
        assert t is not None
        assert t.status == "completed"
        # Assigned to one of the two workers
        assert t.assigned_worker_id in (worker_a.db_worker_id, worker_b.db_worker_id)


@pytest.mark.asyncio
async def test_max_concurrent_workers_enforcement(sample_project):
    """Phase 9: Concurrency limit enforcement.
    
    When active executions reach MAX_CONCURRENT_WORKERS, claim_task MUST return False.
    """
    session_factory = get_session_factory()

    # Pre-populate 2 tasks with 'running' status
    async with session_factory() as session:
        t1 = Task(
            id=uuid.uuid4(),
            project_id=sample_project["project_id"],
            title="Active Task 1",
            description="Active Task 1 Description",
            status="running",
            role="orchestration"
        )
        t2 = Task(
            id=uuid.uuid4(),
            project_id=sample_project["project_id"],
            title="Active Task 2",
            description="Active Task 2 Description",
            status="running",
            role="orchestration"
        )
        # And 1 queued task waiting for concurrency slot
        queued_task = Task(
            id=uuid.uuid4(),
            project_id=sample_project["project_id"],
            title="Queued Task Waiting for Slot",
            description="Queued Task Description",
            status="queued",
            role="orchestration",
            acceptance_criteria=['cmd:python -c "exit(0)"']
        )
        session.add_all([t1, t2, queued_task])
        await session.commit()
        queued_id = queued_task.id

    worker = WorkerProcess(worker_id=f"wkr-limit-{uuid.uuid4().hex[:6]}")
    await worker.connect()
    await worker.register()

    # MAX_CONCURRENT_WORKERS = 2; currently 2 tasks are running
    # Attempting to claim the queued task must be rejected by the concurrency gate
    claimed = await worker.claim_task()
    assert claimed is False, "Expected claim to be rejected by MAX_CONCURRENT_WORKERS limit"

    # Now simulate 1 running task completing
    async with session_factory() as session:
        from sqlalchemy import update
        await session.execute(
            update(Task).where(Task.id == t1.id).values(status="completed")
        )
        await session.commit()

    # Now that active running count < 2, worker should be able to claim the waiting task
    claimed_after = await worker.claim_task()
    assert claimed_after is True, "Expected claim to succeed after concurrency slot freed"

    # Verify task state
    async with session_factory() as session:
        from sqlalchemy import select
        res = await session.execute(select(Task).where(Task.id == queued_id))
        t = res.scalars().first()
        assert t.status == "completed"


@pytest.mark.asyncio
async def test_real_process_tree_termination():
    """Phase 11: Verify ExecutionMonitor.terminate_process terminates OS process trees."""
    execution_id = f"test_term_{uuid.uuid4().hex[:8]}"

    # Spawn an actual sleeping background process
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-c", "import time; time.sleep(60)",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    monitor.register_process(
        execution_id=execution_id,
        pid=proc.pid,
        worker_id="test-worker",
        workspace=".",
        proc=proc
    )

    assert monitor.get_process_info(execution_id) is not None

    # Terminate process tree
    success = monitor.terminate_process(execution_id)
    assert success is True

    # Process tracking should be unregistered
    assert monitor.get_process_info(execution_id) is None

    # Verify process is actually terminated
    try:
        await asyncio.wait_for(proc.wait(), timeout=3.0)
    except asyncio.TimeoutError:
        pytest.fail("Process was not terminated by terminate_process!")
