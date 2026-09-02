"""Database service for NexusForge."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
