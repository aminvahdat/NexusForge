"""Database service for NexusForge."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.models import Project, Task
from typing import Optional

import uuid

async def get_task(db_session: AsyncSession, task_id: str) -> Optional[Task]:
    """Get a task by ID."""
    t_uuid = task_id
    try:
        t_uuid = uuid.UUID(str(task_id))
    except (ValueError, AttributeError):
        pass
    result = await db_session.execute(
        select(Task).where(Task.id == t_uuid)
    )
    return result.scalar_one_or_none()

async def get_project(db_session: AsyncSession, project_id: str) -> Optional[Project]:
    """Get a project by ID."""
    p_uuid = project_id
    try:
        p_uuid = uuid.UUID(str(project_id))
    except (ValueError, AttributeError):
        pass
    result = await db_session.execute(
        select(Project).where(Project.id == p_uuid)
    )
    return result.scalar_one_or_none()

async def get_projects(db_session: AsyncSession) -> list[Project]:
    """Get all projects."""
    result = await db_session.execute(select(Project))
    return result.scalars().all()

async def get_database_status(db_session: AsyncSession) -> str:
    """Check database connection status."""
    try:
        result = await db_session.execute(text("SELECT 1"))
        if result.scalar() is not None:
            return "healthy"
        return "unhealthy"
    except Exception:
        return "unhealthy"