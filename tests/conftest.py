"""Pytest fixtures for NexusForge test suite.

Ensures test isolation by clearing transient state (tasks, workers, artifacts)
between test cases so concurrency gates and claiming tests run in a pristine state.
"""

import os
import sys
import pytest
from sqlalchemy import delete

# Ensure repo root and backend directory are in sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "backend"))

from backend.app.db import get_session_factory, init_database
from backend.app.models import Task, Worker, Artifact


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure database schema is created before running test suite."""
    import asyncio
    from backend.app.db import get_engine, init_database
    asyncio.run(init_database())
    engine = get_engine()
    asyncio.run(engine.dispose())


@pytest.fixture(autouse=True)
async def clean_transient_db_state():
    """Ensure clean tasks, workers, and artifacts state before every test."""
    import backend.app.db as db_mod
    if db_mod._engine is not None:
        await db_mod._engine.dispose()
        db_mod._engine = None
        db_mod._session_factory = None

    session_factory = get_session_factory()
    async with session_factory() as session:
        await session.execute(delete(Artifact))
        await session.execute(delete(Task))
        await session.execute(delete(Worker))
        await session.commit()
    yield
    if db_mod._engine is not None:
        await db_mod._engine.dispose()
        db_mod._engine = None
        db_mod._session_factory = None
