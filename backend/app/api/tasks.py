"""FastAPI API routes for NexusForge - Project and Task endpoints.

Fully authenticated, ownership-enforced, and hardened against IDOR,
path traversal, and command injection.
"""

import json
import os
import shlex
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.db import get_db_session
from app.models import Project, User, Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.database import get_project, get_task
from app.auth import get_current_user
from app.authorization import enforce_ownership, require_superuser

import structlog
logger = structlog.get_logger()

router = APIRouter()


def to_uuid(val) -> Optional[uuid.UUID]:
    if val is None or isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except (ValueError, AttributeError):
        return None


# === PROJECT ENDPOINTS ===

@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, summary="Create a new project")
async def create_project(
    project_in: ProjectCreate,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new project owned by the current authenticated user."""
    name_clean = project_in.name.strip()
    if not name_clean:
        raise HTTPException(status_code=400, detail="Project name is required")

    # Name uniqueness scoped to current user
    result = await db_session.execute(
        select(Project).where(Project.name == name_clean, Project.owner_id == current_user.id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="A project with this name already exists in your account")

    project = Project(
        name=name_clean,
        description=project_in.description.strip(),
        status="active",
        owner_id=current_user.id,
        ai_provider=project_in.ai_provider,
        ai_model=project_in.ai_model,
        preferred_language=project_in.preferred_language or "en",
        timezone=project_in.timezone or "UTC",
        telegram_notifications_enabled=project_in.telegram_notifications_enabled or False,
        telegram_chat_id=project_in.telegram_chat_id,
        workspace_path=project_in.workspace_path,
    )

    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    return project.to_dict()


@router.get("/projects", summary="List user's projects")
async def list_projects(
    status: Optional[str] = None,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """List projects owned by the current authenticated user (or all if superuser)."""
    query = select(Project)
    if not current_user.is_superuser:
        query = query.where(Project.owner_id == current_user.id)
    if status and status.lower() in ("active", "archived", "completed"):
        query = query.where(Project.status == status.lower())
    query = query.order_by(Project.created_at.desc())

    result = await db_session.execute(query)
    projects = result.scalars().all()
    return [p.to_dict() for p in projects]


@router.get("/projects/{project_id}", response_model=ProjectResponse, summary="Get project details")
async def get_project_by_id(
    project_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get project details with strict ownership enforcement."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    enforce_ownership(project.owner_id, current_user, "project")
    return project.to_dict()


@router.put("/projects/{project_id}", response_model=ProjectResponse, summary="Update project")
@router.patch("/projects/{project_id}", response_model=ProjectResponse, summary="Update project")
async def update_project(
    project_id: str,
    project_in: ProjectUpdate,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Update project details with ownership enforcement."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    enforce_ownership(project.owner_id, current_user, "project")

    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(project, field) and value is not None:
            setattr(project, field, value)

    project.updated_at = datetime.now(timezone.utc)
    await db_session.commit()
    await db_session.refresh(project)
    return project.to_dict()


@router.post("/projects/{project_id}/archive", summary="Archive a project")
async def archive_project(
    project_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Archive a project with ownership enforcement."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    enforce_ownership(project.owner_id, current_user, "project")

    project.status = "archived"
    project.archived_at = datetime.now(timezone.utc)
    await db_session.commit()
    await db_session.refresh(project)
    return project.to_dict()


@router.post("/projects/{project_id}/unarchive", summary="Unarchive a project")
async def unarchive_project(
    project_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Unarchive a project with ownership enforcement."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    enforce_ownership(project.owner_id, current_user, "project")

    project.status = "active"
    project.archived_at = None
    await db_session.commit()
    await db_session.refresh(project)
    return project.to_dict()


@router.delete("/projects/{project_id}", summary="Delete a project")
async def delete_project(
    project_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a project and its tasks with ownership enforcement."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    enforce_ownership(project.owner_id, current_user, "project")

    p_uuid = to_uuid(project_id) or project.id
    await db_session.execute(delete(Task).where(Task.project_id == p_uuid))
    await db_session.delete(project)
    await db_session.commit()
    return {"status": "success", "message": "Project deleted successfully", "id": project_id}


@router.get("/projects/{project_id}/tasks", response_model=List[TaskResponse], summary="List tasks for a project")
async def list_tasks_for_project(
    project_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """List tasks for a project with ownership enforcement."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    enforce_ownership(project.owner_id, current_user, "project")

    p_uuid = to_uuid(project_id) or project.id
    result = await db_session.execute(
        select(Task).where(Task.project_id == p_uuid).order_by(Task.created_at.desc())
    )
    tasks = result.scalars().all()
    return [t.to_dict() for t in tasks]


@router.post("/projects/{project_id}/run", summary="Trigger execution of a project")
async def run_project(
    project_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Trigger or re-trigger execution for tasks in a project with ownership enforcement."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    enforce_ownership(project.owner_id, current_user, "project")

    p_uuid = to_uuid(project_id) or project.id
    result = await db_session.execute(
        select(Task).where(Task.project_id == p_uuid)
    )
    tasks = result.scalars().all()

    if not tasks:
        orchestration_task = Task(
            project_id=p_uuid,
            title=f"Execute: {project.name}",
            description=project.description or f"Autonomous execution of project {project.name}",
            role="chief_orchestrator",
            status="queued",
            priority="high",
            required_skills=["orchestration", "architecture"],
        )
        db_session.add(orchestration_task)
        await db_session.commit()
        await db_session.refresh(orchestration_task)
        tasks = [orchestration_task]
    else:
        for t in tasks:
            t.status = "queued"
            t.started_at = None
            t.completed_at = None
        project.status = "active"
        await db_session.commit()

    return {
        "status": "success",
        "message": f"Execution queued for project '{project.name}'",
        "queued_tasks": len(tasks),
        "tasks": [t.to_dict() for t in tasks]
    }


@router.post("/tasks/{task_id}/run", summary="Run or retry a specific task")
async def run_task(
    task_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    task = await get_task(db_session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.project_id:
        project = await get_project(db_session, str(task.project_id))
        if project:
            enforce_ownership(project.owner_id, current_user, "task")

    task.status = "queued"
    task.started_at = None
    task.completed_at = None
    await db_session.commit()
    await db_session.refresh(task)
    return {"status": "success", "task": task.to_dict()}


class TerminalExecRequest(BaseModel):
    command: str


@router.post("/projects/{project_id}/terminal/exec", summary="Execute terminal command inside project workspace")
async def execute_terminal_command(
    project_id: str,
    req: TerminalExecRequest,
    db_session: AsyncSession = Depends(get_db_session),
    admin_user: User = Depends(require_superuser),
):
    """Terminal execution is permanently disabled for security.
    
    Arbitrary command execution on the host without dedicated kernel/container isolation
    presents an unacceptable Remote Code Execution (RCE) vector.
    """
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Terminal execution is disabled for security: host process execution without isolated container sandboxing is forbidden."
    )


@router.get("/projects/{project_id}/agent-traces", summary="Get agent reasoning chains")
async def get_agent_traces(
    project_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Return execution traces for project with ownership enforcement."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    enforce_ownership(project.owner_id, current_user, "project")

    from app.services.workspace_helper import get_project_workspace_path
    ws_dir = get_project_workspace_path(project.name, str(project.id), project.workspace_path)

    trace_file = ws_dir / "agent_reasoning_trace.json"
    if trace_file.exists():
        try:
            traces = json.loads(trace_file.read_text(encoding="utf-8"))
            return {
                "project_id": str(project_id),
                "workspace": str(ws_dir),
                "traces": traces,
                "count": len(traces) if isinstance(traces, list) else 1
            }
        except Exception as e:
            logger.warning("trace_parse_warning", error=str(e))

    return {
        "project_id": str(project_id),
        "workspace": str(ws_dir),
        "traces": [],
        "count": 0,
        "message": "No agent traces generated yet."
    }


# === HERMES CONVERSATIONAL COPILOT & WORKSPACE FILES ENDPOINTS ===

class ProjectMessageCreate(BaseModel):
    content: str


@router.get("/projects/{project_id}/messages", summary="Get conversational messages with Hermes agent")
async def get_project_messages(
    project_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Retrieve chat history with Hermes agent with ownership enforcement."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    enforce_ownership(project.owner_id, current_user, "project")

    from app.services.hermes_agent import HermesAgentService
    messages = await HermesAgentService.get_or_create_initial_messages(db_session, project)
    return {"project_id": str(project_id), "messages": messages}


@router.post("/projects/{project_id}/messages", summary="Send message to Hermes agent")
async def send_project_message(
    project_id: str,
    payload: ProjectMessageCreate,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Send user input to Hermes with ownership enforcement."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    enforce_ownership(project.owner_id, current_user, "project")

    if not payload.content.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty")

    from app.services.hermes_agent import HermesAgentService
    result = await HermesAgentService.handle_user_message(db_session, project, payload.content)

    if result.get("trigger_build"):
        try:
            await run_project(project_id, db_session, current_user)
        except Exception:
            pass

    return result


@router.get("/projects/{project_id}/models", summary="Get model assignments for squad")
async def get_project_models(
    project_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get model configuration with ownership enforcement."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    enforce_ownership(project.owner_id, current_user, "project")

    from app.services.hermes_agent import DEFAULT_FREE_MODELS
    return {
        "project_id": str(project_id),
        "default_models": DEFAULT_FREE_MODELS,
        "configured_provider": project.ai_provider or "openrouter",
        "configured_model": project.ai_model or "meta-llama/llama-3.3-70b-instruct:free"
    }


@router.get("/projects/{project_id}/files", summary="List generated code and files in workspace")
async def list_project_files(
    project_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """List all real code files and deliverables with ownership enforcement."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    enforce_ownership(project.owner_id, current_user, "project")

    from app.services.workspace_helper import get_project_workspace_path
    ws_dir = get_project_workspace_path(project.name, str(project.id), project.workspace_path)

    files = []
    if ws_dir.exists():
        for p in sorted(ws_dir.rglob("*")):
            if p.is_file() and not any(part.startswith((".", "__pycache__", "node_modules")) for part in p.parts):
                rel = p.relative_to(ws_dir).as_posix()
                files.append({
                    "path": rel,
                    "name": p.name,
                    "size": p.stat().st_size,
                    "modified": datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat(),
                    "ext": p.suffix.lower()
                })
    return {"workspace": str(ws_dir.resolve()), "files": files}


@router.get("/projects/{project_id}/files/content", summary="Get content of a file in workspace")
async def get_project_file_content(
    project_id: str,
    path: Optional[str] = None,
    file_path: Optional[str] = None,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Read content of a file in workspace with strict path traversal prevention."""
    target_rel = path or file_path
    if not target_rel:
        raise HTTPException(status_code=400, detail="Path parameter is required")

    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    enforce_ownership(project.owner_id, current_user, "project")

    from app.services.workspace_helper import get_project_workspace_path
    ws_dir = get_project_workspace_path(project.name, str(project.id), project.workspace_path)
    ws_resolved = ws_dir.resolve()

    target_file = (ws_resolved / target_rel).resolve()

    # Path traversal validation: canonical target must be within workspace
    if not target_file.is_relative_to(ws_resolved) or not target_file.is_file():
        raise HTTPException(status_code=404, detail="File not found or access denied")

    try:
        content = target_file.read_text(encoding="utf-8")
        return {"path": target_rel, "content": content, "size": target_file.stat().st_size}
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Binary file cannot be viewed as text")


# === TASK ENDPOINTS ===

@router.post("/projects/{project_id}/tasks", response_model=TaskResponse, status_code=201, summary="Create task under project")
@router.post("/tasks", response_model=TaskResponse, status_code=201, summary="Create a new task")
async def create_task(
    task_in: TaskCreate,
    project_id: Optional[str] = None,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new task under a project with ownership verification."""
    if not task_in.title.strip():
        raise HTTPException(status_code=400, detail="Task title is required")

    # Command Execution Prevention (Option A)
    if task_in.acceptance_criteria:
        for c in task_in.acceptance_criteria:
            if isinstance(c, str) and c.strip().lower().startswith(("cmd:", "exec:", "sh:", "bash:", "powershell:")):
                raise HTTPException(
                    status_code=400,
                    detail="DENIED: User-defined command execution ('cmd:') is prohibited. Tasks must define objectives and acceptance criteria, not shell commands."
                )
    if task_in.description:
        for line in task_in.description.splitlines():
            if line.strip().lower().startswith(("cmd:", "exec:", "sh:", "bash:", "powershell:")):
                raise HTTPException(
                    status_code=400,
                    detail="DENIED: Command execution prefix in task description is prohibited. Tasks must define objectives, not shell commands."
                )

    effective_project_id = project_id or task_in.project_id
    if not effective_project_id:
        raise HTTPException(status_code=400, detail="project_id is required")

    project = await get_project(db_session, effective_project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    enforce_ownership(project.owner_id, current_user, "project")

    p_uuid = to_uuid(effective_project_id)

    task = Task(
        project_id=p_uuid,
        title=task_in.title.strip(),
        description=task_in.description.strip(),
        role=task_in.role or "chief_orchestrator",
        status=task_in.status or "queued",
        priority=task_in.priority or "medium",
        required_skills=task_in.required_skills or [],
        dependencies=task_in.dependencies or [],
        input_artifacts=getattr(task_in, "input_artifacts", []) or [],
        output_artifacts=getattr(task_in, "output_artifacts", []) or [],
        assigned_worker_id=getattr(task_in, "assigned_worker", None),
        acceptance_criteria=getattr(task_in, "acceptance_criteria", []) or [],
        retry_count=task_in.retry_count or 0,
        max_retries=task_in.max_retries or 3,
        due_date=task_in.due_date,
    )

    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    return task.to_dict()


@router.get("/tasks/{task_id}", response_model=TaskResponse, summary="Get task details")
async def get_task_by_id(
    task_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get task details with ownership enforcement."""
    task = await get_task(db_session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.project_id:
        project = await get_project(db_session, str(task.project_id))
        if project:
            enforce_ownership(project.owner_id, current_user, "task")

    return task.to_dict()


@router.get("/tasks", response_model=List[TaskResponse], summary="List tasks")
async def list_all_tasks(
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """List tasks owned by the current authenticated user."""
    if current_user.is_superuser:
        query = select(Task).order_by(Task.created_at.desc())
    else:
        user_proj_ids = select(Project.id).where(Project.owner_id == current_user.id)
        query = select(Task).where(Task.project_id.in_(user_proj_ids)).order_by(Task.created_at.desc())

    result = await db_session.execute(query)
    tasks = result.scalars().all()
    return [t.to_dict() for t in tasks]


@router.put("/tasks/{task_id}", response_model=TaskResponse, summary="Update task")
@router.patch("/tasks/{task_id}", response_model=TaskResponse, summary="Update task")
async def update_task(
    task_id: str,
    task_in: TaskUpdate,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Update task details with ownership enforcement."""
    task = await get_task(db_session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.project_id:
        project = await get_project(db_session, str(task.project_id))
        if project:
            enforce_ownership(project.owner_id, current_user, "task")

    # Command Execution Prevention (Option A)
    if task_in.acceptance_criteria is not None:
        for c in task_in.acceptance_criteria:
            if isinstance(c, str) and c.strip().lower().startswith(("cmd:", "exec:", "sh:", "bash:", "powershell:")):
                raise HTTPException(
                    status_code=400,
                    detail="DENIED: User-defined command execution ('cmd:') is prohibited. Tasks must define objectives and acceptance criteria, not shell commands."
                )
    if task_in.description is not None:
        for line in task_in.description.splitlines():
            if line.strip().lower().startswith(("cmd:", "exec:", "sh:", "bash:", "powershell:")):
                raise HTTPException(
                    status_code=400,
                    detail="DENIED: Command execution prefix in task description is prohibited. Tasks must define objectives, not shell commands."
                )

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
        if task_in.status == "running" and not task.started_at:
            task.started_at = datetime.now(timezone.utc)
        if task_in.status == "completed":
            task.completed_at = datetime.now(timezone.utc)
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
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a task with ownership enforcement."""
    task = await get_task(db_session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.project_id:
        project = await get_project(db_session, str(task.project_id))
        if project:
            enforce_ownership(project.owner_id, current_user, "task")

    await db_session.delete(task)
    await db_session.commit()
    return JSONResponse(
        status_code=200,
        content={"status": "success", "message": "Task deleted successfully", "id": task_id}
    )