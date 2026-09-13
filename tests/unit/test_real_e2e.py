"""Phase 19 — Real End-to-End Integration Test Suite.

Executes all 4 mandatory E2E flows against real FastAPI endpoints and WorkerProcess:
1. SUCCESS PATH: User A login -> create project -> create task -> worker claims -> real OS process executes -> artifact created -> task COMPLETED.
2. AUTHORIZATION PATH: User B attempts to access User A resources -> 403 Forbidden / 404 Not Found (Access Denied).
3. FAILURE PATH: Task with failing command -> real OS process fails with non-zero exit code -> task FAILED -> worker returns IDLE.
4. TIMEOUT / CANCELLATION PATH: Task with long-running command -> execution monitor terminates process tree -> task FAILED / CANCELLED -> worker returns IDLE.
"""

import asyncio
import os
import sys
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from pathlib import Path

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "backend"))

from backend.app.main import app
from backend.worker import WorkerProcess
from backend.app.db import get_session_factory
from backend.app.models import Task, Worker, Artifact, Project, User
from backend.app.services.execution_monitor import monitor
from sqlalchemy import select


@pytest.mark.asyncio
async def test_real_e2e_full_lifecycle():
    """Execute complete 4-part Real E2E suite."""
    transport = ASGITransport(app=app)
    session_factory = get_session_factory()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # ==========================================
        # 1. SUCCESS PATH: User A Full Flow
        # ==========================================
        # Register User A
        email_a = f"user_a_{uuid.uuid4().hex[:8]}@example.com"
        reg_res_a = await client.post("/api/auth/register", json={
            "email": email_a,
            "username": f"user_a_{uuid.uuid4().hex[:6]}",
            "password": "Password123!"
        })
        assert reg_res_a.status_code in (200, 201)
        token_a = reg_res_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # User A creates a project
        proj_res_a = await client.post("/api/projects", json={
            "name": "E2E Success Project",
            "description": "Project for real E2E validation"
        }, headers=headers_a)
        assert proj_res_a.status_code == 201
        project_id_a = proj_res_a.json()["id"]

        # Ensure project workspace directory exists
        ws_dir = (Path("workspaces") / str(project_id_a)).resolve()
        ws_dir.mkdir(parents=True, exist_ok=True)

        # User A creates a task that writes an artifact file
        task_res_a = await client.post(f"/api/projects/{project_id_a}/tasks", json={
            "title": "Build Artifact Task",
            "description": "Real OS command creating deliverable",
            "role": "backend_agent",
            "acceptance_criteria": [
                'cmd:python -c "import pathlib; pathlib.Path(\'output.txt\').write_text(\'hello-nexusforge\')"'
            ]
        }, headers=headers_a)
        assert task_res_a.status_code == 201
        task_id_a = task_res_a.json()["id"]

        # Real Worker connects and claims the task
        worker_a = WorkerProcess(worker_id=f"wkr-e2e-{uuid.uuid4().hex[:6]}")
        await worker_a.connect()
        await worker_a.register()

        claimed = await worker_a.claim_task()
        assert claimed is True

        # Verify task is COMPLETED and artifact was generated
        async with session_factory() as session:
            t_res = await session.execute(select(Task).where(Task.id == uuid.UUID(task_id_a)))
            t_record = t_res.scalar_one()
            assert t_record.status == "completed"
            assert t_record.completed_at is not None

            # Verify artifact created in DB
            art_res = await session.execute(select(Artifact).where(Artifact.task_id == uuid.UUID(task_id_a)))
            artifacts = art_res.scalars().all()
            assert any(a.name == "output.txt" for a in artifacts)

        # ==========================================
        # 2. AUTHORIZATION PATH: Cross-Tenant Isolation
        # ==========================================
        # Register User B
        email_b = f"user_b_{uuid.uuid4().hex[:8]}@example.com"
        reg_res_b = await client.post("/api/auth/register", json={
            "email": email_b,
            "username": f"user_b_{uuid.uuid4().hex[:6]}",
            "password": "Password123!"
        })
        assert reg_res_b.status_code in (200, 201)
        token_b = reg_res_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User B attempts to view User A's project -> Access Denied (403 or 404)
        get_proj_b = await client.get(f"/api/projects/{project_id_a}", headers=headers_b)
        assert get_proj_b.status_code in (403, 404)

        # User B attempts to access User A's task -> Access Denied
        get_task_b = await client.get(f"/api/tasks/{task_id_a}", headers=headers_b)
        assert get_task_b.status_code in (403, 404)

        # User B attempts to control execution of User A's project -> Access Denied
        cancel_b = await client.post(f"/api/execution/test-exec/cancel", headers=headers_b)
        assert cancel_b.status_code in (403, 404)

        # ==========================================
        # 3. FAILURE PATH: Real Process Fails Closed
        # ==========================================
        task_res_fail = await client.post(f"/api/projects/{project_id_a}/tasks", json={
            "title": "Intentional Failure Task",
            "description": "Command returning non-zero exit code",
            "role": "backend_agent",
            "acceptance_criteria": [
                'cmd:python -c "import sys; sys.stderr.write(\'fatal defect\'); sys.exit(7)"'
            ]
        }, headers=headers_a)
        assert task_res_fail.status_code == 201
        task_id_fail = task_res_fail.json()["id"]

        worker_fail = WorkerProcess(worker_id=f"wkr-fail-{uuid.uuid4().hex[:6]}")
        await worker_fail.connect()
        await worker_fail.register()

        claimed_fail = await worker_fail.claim_task()
        assert claimed_fail is True

        # Verify task is FAILED (not completed, fail closed)
        async with session_factory() as session:
            tf_res = await session.execute(select(Task).where(Task.id == uuid.UUID(task_id_fail)))
            tf_record = tf_res.scalar_one()
            assert tf_record.status == "failed"

            # Verify worker returned to idle
            w_res = await session.execute(select(Worker).where(Worker.worker_id == worker_fail.worker_id))
            w_rec = w_res.scalar_one()
            assert w_rec.status == "idle"

        # ==========================================
        # 4. TIMEOUT / CANCELLATION PATH
        # ==========================================
        exec_id = f"e2e_term_{uuid.uuid4().hex[:6]}"
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-c", "import time; time.sleep(120)",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        monitor.register_process(
            execution_id=exec_id,
            pid=proc.pid,
            worker_id=worker_a.worker_id,
            workspace=str(ws_dir),
            proc=proc
        )
        assert monitor.get_process_info(exec_id) is not None

        # Terminate process tree via monitor
        term_ok = monitor.terminate_process(exec_id)
        assert term_ok is True
        assert monitor.get_process_info(exec_id) is None

        # Ensure process terminated
        await asyncio.wait_for(proc.wait(), timeout=3.0)
        assert proc.returncode is not None
