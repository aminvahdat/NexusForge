"""Database service for NexusForge."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.models.task import Task
from app.models import Project
from typing import Optional

async def get_task(db_session: AsyncSession, task_id: str) -> Optional[Task]:
    """Get a task by ID."""
    result = await db_session.execute(
        select(Task).where(Task.id == task_id)
    )
    return result.scalar_one_or_none()

async def get_project(db_session: AsyncSession, project_id: str) -> Optional[Project]:
    """Get a project by ID."""
    result = await db_session.execute(
        select(Project).where(Project.id == project_id)
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