"""FastAPI API routes for NexusForge - Project and Task endpoints."""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.db import get_db_session
from app.models import Project, Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.database import get_project, get_task, get_projects
from app.services.redis import get_redis
import structlog

logger = structlog.get_logger()
router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
async def health() -> Dict[str, Any]:
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/readiness", response_model=Dict[str, Any])
async def readiness(
    db_session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Readiness check — verifies DB and Redis connectivity."""
    try:
        await db_session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    try:
        redis = await get_redis()
        await redis.ping()
        redis_ok = True
    except Exception:
        redis_ok = False

    return {
        "status": "ok" if (db_ok and redis_ok) else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {"database": db_ok, "redis": redis_ok},
    }


@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    db_session: AsyncSession = Depends(get_db_session),
) -> List[ProjectResponse]:
    """List all projects."""
    projects = await get_projects(db_session)
    return [ProjectResponse.model_validate(p) for p in projects]

@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    db_session: AsyncSession = Depends(get_db_session),
) -> ProjectResponse:
    """Create a new project."""
    try:
        db_project = Project(
            name=project.name,
            description=project.description,
            status=project.status,
            owner_id=project.owner_id,
            ai_provider=project.ai_provider,
            ai_model=project.ai_model,
            preferred_language=project.preferred_language,
            timezone=project.timezone,
            telegram_notifications_enabled=project.telegram_notifications_enabled,
            telegram_chat_id=project.telegram_chat_id,
        )
        db_session.add(db_project)
        await db_session.commit()
        await db_session.refresh(db_project)
        return ProjectResponse.model_validate(db_project)
    except Exception as e:
        logger.error("create_project_failed", error=str(e))
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="Failed to create project")


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project_endpoint(
    project_id: str,
    db_session: AsyncSession = Depends(get_db_session),
) -> ProjectResponse:
    """Get a project by ID."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.model_validate(project)


@router.post("/projects/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: str,
    task: TaskCreate,
    db_session: AsyncSession = Depends(get_db_session),
) -> TaskResponse:
    """Create a task for a project."""
    try:
        db_task = Task(
            project_id=project_id,
            title=task.title,
            description=task.description,
            role=task.role,
            status=task.status,
            priority=task.priority,
            required_skills=task.required_skills,
            dependencies=task.dependencies,
            input_artifacts=task.input_artifacts,
            output_artifacts=task.output_artifacts,
            acceptance_criteria=task.acceptance_criteria,
            retry_count=task.retry_count,
            max_retries=task.max_retries,
            due_date=task.due_date,
        )
        db_session.add(db_task)
        await db_session.commit()
        await db_session.refresh(db_task)
        return TaskResponse.model_validate(db_task)
    except Exception as e:
        logger.error("create_task_failed", error=str(e))
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="Failed to create task")


@router.get("/projects/{project_id}/tasks", response_model=List[TaskResponse])
async def list_tasks(
    project_id: str,
    status: Optional[str] = None,
    db_session: AsyncSession = Depends(get_db_session),
) -> List[TaskResponse]:
    """List tasks for a project."""
    try:
        query = select(Task).where(Task.project_id == project_id)
        if status:
            query = query.where(Task.status == status)
        query = query.order_by(Task.created_at.desc())
        result = await db_session.execute(query)
        tasks = result.scalars().all()
        return [TaskResponse.model_validate(t) for t in tasks]
    except Exception as e:
        logger.error("list_tasks_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list tasks")


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_endpoint(
    task_id: str,
    db_session: AsyncSession = Depends(get_db_session),
) -> TaskResponse:
    """Get a task by ID."""
    task = await get_task(db_session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse.model_validate(task)


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    db_session: AsyncSession = Depends(get_db_session),
) -> TaskResponse:
    """Update a task."""
    task = await get_task(db_session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        update_data = task_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(task, key, value)
        if task_update.status == "running" and not task.started_at:
            task.started_at = datetime.now(timezone.utc)
        if task_update.status == "completed":
            task.completed_at = datetime.now(timezone.utc)
        await db_session.commit()
        await db_session.refresh(task)
        return TaskResponse.model_validate(task)
    except Exception as e:
        logger.error("update_task_failed", error=str(e))
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="Failed to update task")


@router.get("/workers/status", response_model=Dict[str, Any])
async def get_workers_status() -> Dict[str, Any]:
    """Get worker pool status."""
    return {"status": "ok", "pool_size": 2}