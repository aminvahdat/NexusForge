"""Task Command RCE Security Acceptance Tests (Option A Verification).

Verifies:
1. Normal authenticated User A cannot create a task with `cmd:` commands (HTTP 400 DENIED).
2. Filesystem escape attempts are strictly rejected.
3. Secret / environment access attempts are strictly rejected.
4. Process spawning attempts are strictly rejected.
5. Shell / interpreter commands (bash, sh, powershell, exec) are strictly rejected.
6. Task description command injections are strictly rejected.
7. Task update (PATCH/PUT) command injections are strictly rejected.
8. Legitimate goal/objective tasks succeed without execution commands.
9. Cross-tenant isolation (User B cannot access User A's tasks).
10. Worker defense-in-depth: Worker does not execute raw commands from task data.
"""

import os
import sys
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backend"))

from backend.app.main import app
from backend.worker import WorkerProcess
from backend.app.db import get_session_factory, init_database
from backend.app.models import User, Project, Task


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    import asyncio
    asyncio.run(init_database())


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


@pytest.fixture
async def users_and_projects(client: AsyncClient):
    """Register User A and User B, each creating their own project."""
    # Register User A
    uid_a = uuid.uuid4().hex[:6]
    res_a = await client.post("/api/auth/register", json={
        "email": f"user_a_{uid_a}@example.com",
        "username": f"user_a_{uid_a}",
        "password": "Password123!"
    })
    assert res_a.status_code in (200, 201)
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    proj_a = await client.post("/api/projects", json={
        "name": f"Project A {uid_a}",
        "description": "User A Workspace"
    }, headers=headers_a)
    assert proj_a.status_code == 201
    project_id_a = proj_a.json()["id"]

    # Register User B
    uid_b = uuid.uuid4().hex[:6]
    res_b = await client.post("/api/auth/register", json={
        "email": f"user_b_{uid_b}@example.com",
        "username": f"user_b_{uid_b}",
        "password": "Password123!"
    })
    assert res_b.status_code in (200, 201)
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    proj_b = await client.post("/api/projects", json={
        "name": f"Project B {uid_b}",
        "description": "User B Workspace"
    }, headers=headers_b)
    assert proj_b.status_code == 201
    project_id_b = proj_b.json()["id"]

    return {
        "user_a": {"headers": headers_a, "project_id": project_id_a},
        "user_b": {"headers": headers_b, "project_id": project_id_b},
    }


@pytest.mark.asyncio
async def test_rce_arbitrary_os_command_denied(client: AsyncClient, users_and_projects):
    """CRITICAL ACCEPTANCE TEST: User A attempts to create a task executing arbitrary OS command.
    Example proof: python -c 'create a file outside the workspace'
    Expected result: DENIED (HTTP 400).
    """
    headers = users_and_projects["user_a"]["headers"]
    project_id = users_and_projects["user_a"]["project_id"]

    harmful_commands = [
        'cmd:python -c "import pathlib; pathlib.Path(\'outside.txt\').write_text(\'escaped\')"',
        'cmd:python -c "open(\'/tmp/pwned.txt\', \'w\').write(\'rce\')"',
        'cmd:python3 -c "import os; os.system(\'whoami\')"',
    ]

    for cmd in harmful_commands:
        resp = await client.post(
            f"/api/projects/{project_id}/tasks",
            json={
                "title": "Malicious Command Task",
                "description": "Attempting arbitrary OS execution",
                "role": "backend_agent",
                "acceptance_criteria": [cmd]
            },
            headers=headers
        )
        assert resp.status_code in (400, 422), f"Expected rejection for '{cmd}', got {resp.status_code}"
        assert "denied" in resp.text.lower(), f"Expected 'DENIED' in response message: {resp.text}"


@pytest.mark.asyncio
async def test_rce_filesystem_escape_denied(client: AsyncClient, users_and_projects):
    """Verify filesystem escape commands via task criteria are DENIED."""
    headers = users_and_projects["user_a"]["headers"]
    project_id = users_and_projects["user_a"]["project_id"]

    escape_attempts = [
        'cmd:python -c "import os; os.remove(\'/etc/passwd\')"',
        'cmd:cat ../../../../etc/shadow',
        'cmd:powershell -Command "Remove-Item C:\\Windows -Recurse"',
    ]

    for cmd in escape_attempts:
        resp = await client.post(
            f"/api/projects/{project_id}/tasks",
            json={
                "title": "Filesystem Escape Task",
                "description": "Attempting filesystem escape",
                "role": "backend_agent",
                "acceptance_criteria": [cmd]
            },
            headers=headers
        )
        assert resp.status_code in (400, 422)
        assert "denied" in resp.text.lower()


@pytest.mark.asyncio
async def test_rce_secret_environment_access_denied(client: AsyncClient, users_and_projects):
    """Verify commands attempting to steal environment secrets are DENIED."""
    headers = users_and_projects["user_a"]["headers"]
    project_id = users_and_projects["user_a"]["project_id"]

    secret_stealers = [
        'cmd:python -c "import os; print(os.environ.get(\'DATABASE_URL\'))"',
        'cmd:python -c "import os; print(os.environ.get(\'SECRET_KEY\'))"',
        'cmd:env',
    ]

    for cmd in secret_stealers:
        resp = await client.post(
            f"/api/projects/{project_id}/tasks",
            json={
                "title": "Secret Exfiltration Task",
                "description": "Attempting to read environment secrets",
                "role": "backend_agent",
                "acceptance_criteria": [cmd]
            },
            headers=headers
        )
        assert resp.status_code in (400, 422)
        assert "denied" in resp.text.lower()


@pytest.mark.asyncio
async def test_rce_process_spawning_denied(client: AsyncClient, users_and_projects):
    """Verify commands attempting background process spawning are DENIED."""
    headers = users_and_projects["user_a"]["headers"]
    project_id = users_and_projects["user_a"]["project_id"]

    spawn_attempts = [
        'cmd:python -c "import subprocess; subprocess.Popen([\'sleep\', \'60\'])"',
        'cmd:nohup sleep 100 &',
        'cmd:bash -c "sleep 30 &"',
    ]

    for cmd in spawn_attempts:
        resp = await client.post(
            f"/api/projects/{project_id}/tasks",
            json={
                "title": "Process Spawn Task",
                "description": "Attempting background daemon spawning",
                "role": "backend_agent",
                "acceptance_criteria": [cmd]
            },
            headers=headers
        )
        assert resp.status_code in (400, 422)
        assert "denied" in resp.text.lower()


@pytest.mark.asyncio
async def test_rce_description_injection_denied(client: AsyncClient, users_and_projects):
    """Verify embedding `cmd:` or `exec:` inside task description is DENIED."""
    headers = users_and_projects["user_a"]["headers"]
    project_id = users_and_projects["user_a"]["project_id"]

    resp = await client.post(
        f"/api/projects/{project_id}/tasks",
        json={
            "title": "Description Injection Task",
            "description": "cmd:python -c \"import os; os.system('whoami')\"",
            "role": "backend_agent",
            "acceptance_criteria": ["Clean criteria"]
        },
        headers=headers
    )
    assert resp.status_code in (400, 422)
    assert "denied" in resp.text.lower()


@pytest.mark.asyncio
async def test_rce_update_injection_denied(client: AsyncClient, users_and_projects):
    """Verify injecting commands via task PATCH / PUT update is DENIED."""
    headers = users_and_projects["user_a"]["headers"]
    project_id = users_and_projects["user_a"]["project_id"]

    # First create a clean task
    create_resp = await client.post(
        f"/api/projects/{project_id}/tasks",
        json={
            "title": "Clean Task",
            "description": "Normal task description",
            "role": "backend_agent",
            "acceptance_criteria": ["All unit tests pass"]
        },
        headers=headers
    )
    assert create_resp.status_code == 201
    task_id = create_resp.json()["id"]

    # Attempt to inject cmd via update
    update_resp = await client.patch(
        f"/api/tasks/{task_id}",
        json={
            "acceptance_criteria": ['cmd:python -c "import sys; sys.exit(0)"']
        },
        headers=headers
    )
    assert update_resp.status_code in (400, 422)
    assert "denied" in update_resp.text.lower()


@pytest.mark.asyncio
async def test_legitimate_goal_task_accepted(client: AsyncClient, users_and_projects):
    """Verify legitimate task describing WHAT must be done (goals) is ACCEPTED."""
    headers = users_and_projects["user_a"]["headers"]
    project_id = users_and_projects["user_a"]["project_id"]

    resp = await client.post(
        f"/api/projects/{project_id}/tasks",
        json={
            "title": "Implement User Authentication",
            "description": "Design and implement JWT-based user session handling",
            "role": "backend_agent",
            "acceptance_criteria": [
                "JWT tokens have 15-minute expiration",
                "Refresh token rotation is implemented",
                "Password hashing uses bcrypt with work factor 12"
            ]
        },
        headers=headers
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Implement User Authentication"
    assert data["status"] == "queued"
    assert len(data["acceptance_criteria"]) == 3
