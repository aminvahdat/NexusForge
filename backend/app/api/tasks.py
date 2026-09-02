"""FastAPI API routes for NexusForge - Project and Task endpoints."""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db_session
from app.models.task import Task
from app.models import Project
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.database import get_project, get_task


router = APIRouter()


# === PROJECT ENDPOINTS ===

@router.post("/projects", response_model=ProjectResponse, status_code=201, summary="Create a new project")
async def create_project(
    project_in: ProjectCreate,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Create a new project."""
    if not project_in.name.strip():
        raise HTTPException(status_code=400, detail="Project name is required")
    
    result = await db_session.execute(
        select(Project).where(Project.name == project_in.name)
    )
    if result.scalar():
        raise HTTPException(status_code=409, detail="Project name already exists")
    
    project = Project(
        name=project_in.name,
        description=project_in.description,
        owner_id=project_in.owner_id,
        ai_provider=project_in.ai_provider,
        ai_model=project_in.ai_model,
        preferred_language=project_in.preferred_language,
        timezone=project_in.timezone,
        telegram_notifications_enabled=project_in.telegram_notifications_enabled,
        telegram_chat_id=project_in.telegram_chat_id,
    )
    
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    
    return project.to_dict()


@router.get("/projects/{project_id}", response_model=ProjectResponse, summary="Get project details")
async def get_project_by_id(
    project_id: str,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Get project details."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project.to_dict()


@router.get("/projects", summary="List user's projects")
async def list_projects(
    db_session: AsyncSession = Depends(get_db_session)
):
    """List user's projects."""
    result = await db_session.execute(
        select(Project).order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    return [project.to_dict() for project in projects]


@router.get("/projects/{project_id}/tasks", response_model=List[TaskResponse], summary="List tasks for a project")
async def list_tasks(
    project_id: str,
    db_session: AsyncSession = Depends(get_db_session)
):
    """List tasks for a specific project."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    result = await db_session.execute(
        select(Task).where(Task.project_id == project_id)
    )
    tasks = result.scalars().all()
    return [task.to_dict() for task in tasks]


# === TASK ENDPOINTS ===

@router.post("/tasks", response_model=TaskResponse, status_code=201, summary="Create a new task")
async def create_task(
    task_in: TaskCreate,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Create a new task."""
    if not task_in.title.strip():
        raise HTTPException(status_code=400, detail="Task title is required")
    
    for dep_id in task_in.dependencies:
        dep_task = await get_task(db_session, dep_id)
        if not dep_task:
            raise HTTPException(status_code=404, detail=f"Dependency task {dep_id} not found")
    
    task = Task(
        id=task_in.task_id,
        project_id=task_in.project_id,
        title=task_in.title,
        description=task_in.description,
        role=task_in.role,
        required_skills=task_in.required_skills,
        dependencies=task_in.dependencies,
        input_artifacts=task_in.input_artifacts,
        output_artifacts=task_in.output_artifacts,
        assigned_worker_id=task_in.assigned_worker,
        acceptance_criteria=task_in.acceptance_criteria,
        retry_count=task_in.retry_count,
        max_retries=task_in.max_retries,
        due_date=task_in.due_date,
    )
    
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    
    return task.to_dict()


@router.get("/tasks/{task_id}", response_model=TaskResponse, summary="Get task details")
async def get_task_by_id(
    task_id: str,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Get task details."""
    task = await get_task(db_session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@router.patch("/tasks/{task_id}", response_model=TaskResponse, summary="Update task")
async def update_task(
    task_id: str,
    task_in: TaskUpdate,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Update task details."""
    task = await get_task(db_session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task_in.title is not None:
        task.title = task_in.title
    if task_in.description is not None:
        task.description = task_in.description
    if task_in.role is not None:
        task.role = task_in.role
    if task_in.priority is not None:
        task.priority = task_in.priority
    if task_in.status is not None:
        task.status = task_in.status
    if task_in.dependencies is not None:
        task.dependencies = task_in.dependencies
    if task_in.input_artifacts is not None:
        task.input_artifacts = task_in.input_artifacts
    if task_in.output_artifacts is not None:
        task.output_artifacts = task_in.output_artifacts
    if task_in.acceptance_criteria is not None:
        task.acceptance_criteria = task_in.acceptance_criteria
    if task_in.retry_count is not None:
        task.retry_count = task_in.retry_count
    if task_in.max_retries is not None:
        task.max_retries = task_in.max_retries
    if task_in.due_date is not None:
        task.due_date = task_in.due_date
    
    task.updated_at = datetime.now(timezone.utc)
    
    await db_session.commit()
    await db_session.refresh(task)
    
    return task.to_dict()


@router.delete("/tasks/{task_id}", summary="Delete a task")
async def delete_task(
    task_id: str,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Delete a task."""
    task = await get_task(db_session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await db_session.delete(task)
    await db_session.commit()
    return JSONResponse(
        status_code=204,
        content={"status": "success", "message": "Task deleted successfully"}
    )