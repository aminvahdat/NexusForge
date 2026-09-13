"""Security Audit Test Suite for NexusForge.

Verifies:
1. Fail-closed authentication (401 on missing, invalid, or expired tokens)
2. IDOR prevention across multi-user project/task boundaries (403 on cross-tenant access)
3. Path traversal attack prevention on workspace file endpoints
4. Command injection & RCE mitigation on /terminal/exec (non-superuser rejected, allowlist enforced)
"""

import os
import sys
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backend"))

from backend.app.main import app
from backend.app.auth import create_access_token, get_password_hash
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
async def test_users():
    session_factory = get_session_factory()
    async with session_factory() as session:
        # Create User 1
        u1_id = uuid.uuid4()
        user1 = User(
            id=u1_id,
            email=f"user1_{u1_id.hex[:8]}@example.com",
            username=f"user1_{u1_id.hex[:8]}",
            password_hash=get_password_hash("Secret123!"),
            is_active=True,
            is_superuser=False
        )
        session.add(user1)

        # Create User 2
        u2_id = uuid.uuid4()
        user2 = User(
            id=u2_id,
            email=f"user2_{u2_id.hex[:8]}@example.com",
            username=f"user2_{u2_id.hex[:8]}",
            password_hash=get_password_hash("Secret123!"),
            is_active=True,
            is_superuser=False
        )
        session.add(user2)

        # Create Superuser
        admin_id = uuid.uuid4()
        admin_user = User(
            id=admin_id,
            email=f"admin_{admin_id.hex[:8]}@example.com",
            username=f"admin_{admin_id.hex[:8]}",
            password_hash=get_password_hash("AdminPass123!"),
            is_active=True,
            is_superuser=True
        )
        session.add(admin_user)
        await session.commit()

        token1 = create_access_token({"sub": str(u1_id), "email": user1.email})
        token2 = create_access_token({"sub": str(u2_id), "email": user2.email})
        admin_token = create_access_token({"sub": str(admin_id), "email": admin_user.email})

        return {
            "user1": {"id": u1_id, "token": token1},
            "user2": {"id": u2_id, "token": token2},
            "admin": {"id": admin_id, "token": admin_token},
        }


@pytest.mark.asyncio
async def test_unauthenticated_requests_fail_closed(client: AsyncClient):
    """Verify all protected endpoints return 401 without Bearer token."""
    endpoints = [
        ("GET", "/api/projects"),
        ("GET", "/api/settings/keys"),
        ("GET", "/api/workers"),
        ("GET", "/api/artifacts/project/00000000-0000-0000-0000-000000000000"),
        ("GET", "/api/execution/list"),
    ]
    for method, path in endpoints:
        resp = await client.request(method, path)
        assert resp.status_code == 401, f"Expected 401 on unauthenticated {method} {path}, got {resp.status_code}"


@pytest.mark.asyncio
async def test_invalid_and_expired_tokens_fail_closed(client: AsyncClient):
    """Verify malformed and expired JWTs are rejected with 401."""
    # Malformed token
    resp = await client.get("/api/projects", headers={"Authorization": "Bearer not-a-valid-token"})
    assert resp.status_code == 401

    # Expired token
    expired_token = create_access_token(
        {"sub": str(uuid.uuid4())},
        expires_delta=timedelta(seconds=-60)
    )
    resp = await client.get("/api/projects", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_idor_cross_tenant_isolation(client: AsyncClient, test_users):
    """Verify User 2 cannot access or delete User 1's project."""
    u1_headers = {"Authorization": f"Bearer {test_users['user1']['token']}"}
    u2_headers = {"Authorization": f"Bearer {test_users['user2']['token']}"}

    # User 1 creates project
    p_resp = await client.post(
        "/api/projects",
        json={"name": f"P1_{uuid.uuid4().hex[:6]}", "description": "Private User 1 Project"},
        headers=u1_headers
    )
    assert p_resp.status_code in (200, 201)
    project_id = p_resp.json()["id"]

    # User 2 attempts to read User 1's project -> 403 Forbidden
    get_resp = await client.get(f"/api/projects/{project_id}", headers=u2_headers)
    assert get_resp.status_code == 403, f"Expected 403 IDOR rejection, got {get_resp.status_code}"

    # User 2 attempts to delete User 1's project -> 403 Forbidden
    del_resp = await client.delete(f"/api/projects/{project_id}", headers=u2_headers)
    assert del_resp.status_code == 403, f"Expected 403 IDOR rejection, got {del_resp.status_code}"

    # User 1 can read own project
    u1_get = await client.get(f"/api/projects/{project_id}", headers=u1_headers)
    assert u1_get.status_code == 200


@pytest.mark.asyncio
async def test_path_traversal_prevention(client: AsyncClient, test_users):
    """Verify path traversal outside project workspace is blocked with 400/403."""
    u1_headers = {"Authorization": f"Bearer {test_users['user1']['token']}"}

    p_resp = await client.post(
        "/api/projects",
        json={"name": f"P_Trav_{uuid.uuid4().hex[:6]}", "description": "Traversal Test"},
        headers=u1_headers
    )
    project_id = p_resp.json()["id"]

    # Attempt path traversal
    traversal_paths = [
        "../../../../etc/passwd",
        "..\\..\\..\\Windows\\win.ini",
        "/etc/shadow",
        "nested/../../secret.key"
    ]
    for bad_path in traversal_paths:
        resp = await client.get(
            f"/api/projects/{project_id}/files/content",
            params={"file": bad_path},
            headers=u1_headers
        )
        assert resp.status_code in (400, 403, 404), f"Expected rejection for traversal '{bad_path}', got {resp.status_code}"


@pytest.mark.asyncio
async def test_terminal_exec_rce_prevention(client: AsyncClient, test_users):
    """Verify general host execution on /terminal/exec is permanently disabled (Fail Closed)."""
    u1_headers = {"Authorization": f"Bearer {test_users['user1']['token']}"}
    admin_headers = {"Authorization": f"Bearer {test_users['admin']['token']}"}

    p_resp = await client.post(
        "/api/projects",
        json={"name": f"P_Exec_{uuid.uuid4().hex[:6]}", "description": "Exec Test"},
        headers=u1_headers
    )
    project_id = p_resp.json()["id"]

    # 1. Non-superuser cannot execute terminal commands -> 403 Forbidden
    non_admin_resp = await client.post(
        f"/api/projects/{project_id}/terminal/exec",
        json={"command": "python --version"},
        headers=u1_headers
    )
    assert non_admin_resp.status_code == 403, f"Expected 403 for non-superuser, got {non_admin_resp.status_code}"

    # 2. Superuser is also blocked from general-purpose unisolated execution -> 403 Forbidden (Fail Closed)
    admin_resp = await client.post(
        f"/api/projects/{project_id}/terminal/exec",
        json={"command": "python -c \"import os; os.system('whoami')\""},
        headers=admin_headers
    )
    assert admin_resp.status_code == 403
    assert "disabled for security" in admin_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_execution_control_authorization_idor(client: AsyncClient, test_users):
    """Phase 12: Verify cross-user execution control (retire/cancel, status) is strictly rejected with 403."""
    u1_headers = {"Authorization": f"Bearer {test_users['user1']['token']}"}
    u2_headers = {"Authorization": f"Bearer {test_users['user2']['token']}"}

    # User 1 creates project & task
    p_resp = await client.post(
        "/api/projects",
        json={"name": f"P_ExecCtrl_{uuid.uuid4().hex[:6]}", "description": "Exec Control Test"},
        headers=u1_headers
    )
    project_id = p_resp.json()["id"]

    t_resp = await client.post(
        f"/api/projects/{project_id}/tasks",
        json={"title": "Exec Task 1", "description": "Testing execution ownership", "project_id": project_id},
        headers=u1_headers
    )
    task_id = t_resp.json()["id"]

    # User 1 starts execution
    start_resp = await client.post(f"/api/execution/start/{task_id}", headers=u1_headers)
    assert start_resp.status_code == 200
    execution_id = start_resp.json()["execution_id"]

    # User 2 attempts to retire (cancel) User 1's execution -> 403 Forbidden
    u2_retire = await client.post(f"/api/execution/{execution_id}/retire", headers=u2_headers)
    assert u2_retire.status_code == 403, f"Expected 403 Forbidden for User 2, got {u2_retire.status_code}"

    # User 2 attempts to inspect User 1's execution status -> 403 Forbidden
    u2_status = await client.get(f"/api/execution/status/{execution_id}", headers=u2_headers)
    assert u2_status.status_code == 403, f"Expected 403 Forbidden for User 2, got {u2_status.status_code}"

    # User 1 retires own execution -> 200 OK
    u1_retire = await client.post(f"/api/execution/{execution_id}/retire", headers=u1_headers)
    assert u1_retire.status_code == 200
    assert u1_retire.json()["status"] == "retired"


def test_websocket_subscription_authorization(test_users):
    """Phase 13: Verify WebSocket connection authentication and cross-user execution subscription rejection."""
    from starlette.testclient import TestClient
    from starlette.websockets import WebSocketDisconnect
    from backend.app.main import app

    u1_token = test_users["user1"]["token"]
    u2_token = test_users["user2"]["token"]

    with TestClient(app) as tc:
        # 1. Connection without token fails closed
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with tc.websocket_connect("/api/execution/ws/test-client-no-auth"):
                pass
        assert exc_info.value.code == 1008

        # 2. Connection with invalid token fails closed
        with pytest.raises(WebSocketDisconnect) as exc_info2:
            with tc.websocket_connect("/api/execution/ws/test-client-bad-auth?token=invalid.jwt.token"):
                pass
        assert exc_info2.value.code == 1008

        # 3. Connection with valid token succeeds
        with tc.websocket_connect(f"/api/execution/ws/client-u2?token={u2_token}") as ws2:
            # User 2 attempts to subscribe to an execution not owned by them
            fake_exec_id = "exec_unauthorized_999"
            ws2.send_json({"type": "execution_subscribe", "execution_id": fake_exec_id})
            reply = ws2.receive_json()
            assert reply["type"] == "error"
            assert "unauthorized" in reply["message"].lower()



