"""Unit test for instant unverified signup, /auth/me provider check, and onboarding settings."""

import os
import sys
import uuid
import pytest
from httpx import AsyncClient, ASGITransport

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "backend"))

from backend.app.main import app
from backend.app.db import get_session_factory
from backend.app.models import User
from sqlalchemy import select


@pytest.mark.asyncio
async def test_instant_signup_without_verification():
    """Verify any user can sign up with email and password, immediately active and verified."""
    transport = ASGITransport(app=app)
    session_factory = get_session_factory()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        test_email = f"instant_{uuid.uuid4().hex[:8]}@example.com"
        test_password = "SecurePassword123!"

        # 1. Sign up user
        reg_res = await client.post("/api/auth/register", json={
            "email": test_email,
            "password": test_password,
        })
        assert reg_res.status_code in (200, 201), f"Signup failed: {reg_res.text}"
        data = reg_res.json()
        assert "access_token" in data
        assert data.get("token_type") == "bearer"
        token = data["access_token"]

        # 2. Verify in database: user is active and email_verified=True immediately
        async with session_factory() as session:
            stmt = select(User).where(User.email == test_email)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            assert user is not None
            assert user.is_active is True
            assert user.email_verified is True

        # 3. Check /api/auth/me before configuring AI provider
        headers = {"Authorization": f"Bearer {token}"}
        me_res = await client.get("/api/auth/me", headers=headers)
        assert me_res.status_code == 200
        me_data = me_res.json()
        user_info = me_data.get("user", {})
        assert user_info.get("email") == test_email
        assert user_info.get("email_verified") is True
        # Provider should not be configured yet
        assert user_info.get("has_configured_provider") is False

        # 4. User configures an AI Provider via /api/settings/keys
        key_res = await client.post("/api/settings/keys", json={
            "name": "Onboarding OpenRouter Key",
            "provider": "openrouter",
            "api_key": "sk-or-v1-testkey1234567890abcdef",
            "model": "openrouter/auto",
            "is_active": True,
        }, headers=headers)
        assert key_res.status_code in (200, 201), f"Failed to save key: {key_res.text}"

        # 5. Check /api/auth/me again: has_configured_provider must now be True
        me_res_after = await client.get("/api/auth/me", headers=headers)
        assert me_res_after.status_code == 200
        user_info_after = me_res_after.json().get("user", {})
        assert user_info_after.get("has_configured_provider") is True


@pytest.mark.asyncio
async def test_curated_openrouter_models_available():
    """Verify fallback curated models for openrouter exist for offline resilience."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register a quick user to authenticate
        email = f"curated_{uuid.uuid4().hex[:8]}@example.com"
        reg = await client.post("/api/auth/register", json={"email": email, "password": "Password123!"})
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Fetch models for openrouter
        fetch_res = await client.post("/api/settings/fetch-models", json={
            "provider": "openrouter"
        }, headers=headers)
        assert fetch_res.status_code == 200
        models_data = fetch_res.json()
        assert models_data.get("provider") == "openrouter"
        model_ids = [m["id"] for m in models_data.get("models", [])]
        assert "openrouter/auto" in model_ids or len(model_ids) > 0
