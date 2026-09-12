"""FastAPI API routes for NexusForge - Project and Task endpoints."""

import uuid
from datetime import datetime, timezone
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


router = APIRouter()


def to_uuid(val) -> Optional[uuid.UUID]:
    if val is None or isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except (ValueError, AttributeError):
        return None


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
        select(Project).where(Project.name == project_in.name.strip())
    )
    if result.scalar():
        raise HTTPException(status_code=409, detail="Project name already exists")

    owner_uuid = to_uuid(project_in.owner_id)
    if not owner_uuid:
        admin_res = await db_session.execute(select(User).where(User.email == "admin@nexusforge.io"))
        admin = admin_res.scalar_one_or_none()
        owner_uuid = admin.id if admin else uuid.uuid4()

    project = Project(
        name=project_in.name.strip(),
        description=project_in.description.strip(),
        status="active",
        owner_id=owner_uuid,
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


@router.put("/projects/{project_id}", response_model=ProjectResponse, summary="Update project")
@router.patch("/projects/{project_id}", response_model=ProjectResponse, summary="Update project")
async def update_project(
    project_id: str,
    project_in: ProjectUpdate,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Update project details including workspace path."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(project, field) and value is not None:
            setattr(project, field, value)

    project.updated_at = datetime.utcnow()
    await db_session.commit()
    await db_session.refresh(project)
    return project.to_dict()


@router.get("/projects", summary="List user's projects")
async def list_projects(
    status: Optional[str] = None,
    db_session: AsyncSession = Depends(get_db_session)
):
    """List user's projects with optional status filter."""
    query = select(Project).order_by(Project.created_at.desc())
    if status and status.lower() in ("active", "archived", "completed"):
        query = query.where(Project.status == status.lower())
    result = await db_session.execute(query)
    projects = result.scalars().all()
    return [project.to_dict() for project in projects]


@router.post("/projects/{project_id}/archive", summary="Archive a project")
async def archive_project(
    project_id: str,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Archive a project."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.status = "archived"
    project.archived_at = datetime.now(timezone.utc)
    await db_session.commit()
    await db_session.refresh(project)
    return project.to_dict()


@router.post("/projects/{project_id}/unarchive", summary="Unarchive a project")
async def unarchive_project(
    project_id: str,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Unarchive a project, restoring it to active."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.status = "active"
    project.archived_at = None
    await db_session.commit()
    await db_session.refresh(project)
    return project.to_dict()


@router.delete("/projects/{project_id}", summary="Delete a project")
async def delete_project(
    project_id: str,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Delete a project and all its tasks."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    p_uuid = to_uuid(project_id) or project.id
    await db_session.execute(delete(Task).where(Task.project_id == p_uuid))
    await db_session.delete(project)
    await db_session.commit()
    return {"status": "success", "message": "Project deleted successfully", "id": project_id}


@router.get("/projects/{project_id}/tasks", response_model=List[TaskResponse], summary="List tasks for a project")
async def list_tasks_for_project(
    project_id: str,
    db_session: AsyncSession = Depends(get_db_session)
):
    """List tasks for a specific project."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    p_uuid = to_uuid(project_id) or project.id
    result = await db_session.execute(
        select(Task).where(Task.project_id == p_uuid).order_by(Task.created_at.desc())
    )
    tasks = result.scalars().all()
    return [task.to_dict() for task in tasks]


@router.post("/projects/{project_id}/run", summary="Trigger autonomous execution of a project")
async def run_project(
    project_id: str,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Trigger or re-trigger autonomous execution for all tasks in a project."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    p_uuid = to_uuid(project_id) or project.id
    result = await db_session.execute(
        select(Task).where(Task.project_id == p_uuid)
    )
    tasks = result.scalars().all()

    if not tasks:
        # Auto-create initial orchestration task for Arya
        orchestration_task = Task(
            project_id=p_uuid,
            title=f"هدایت و اجرای خودکار: {project.name}",
            description=project.description or f"Autonomous execution of project {project.name}",
            role="chief_orchestrator",
            status="queued",
            priority="high",
            required_skills=["orchestration", "architecture", "task_delegation"],
            acceptance_criteria=[
                "تحلیل و شکست معماری توسط آریا و تفویض به ایجنت‌ها",
                "پیاده‌سازی ماژول‌ها و راستی‌آزمایی کیفیت"
            ]
        )
        db_session.add(orchestration_task)
        await db_session.commit()
        await db_session.refresh(orchestration_task)
        tasks = [orchestration_task]
    else:
        # Re-queue tasks so worker picks them up
        for t in tasks:
            t.status = "queued"
            t.started_at = None
            t.completed_at = None
        project.status = "active"
        await db_session.commit()

    return {
        "status": "success",
        "message": f"Autonomous execution triggered for project '{project.name}'",
        "queued_tasks": len(tasks),
        "tasks": [t.to_dict() for t in tasks]
    }


@router.post("/tasks/{task_id}/run", summary="Run or retry a specific task")
async def run_task(
    task_id: str,
    db_session: AsyncSession = Depends(get_db_session)
):
    task = await get_task(db_session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
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
    db_session: AsyncSession = Depends(get_db_session)
):
    """Execute command directly in the project workspace directory."""
    import subprocess, time
    from pathlib import Path

    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    from app.services.workspace_helper import get_project_workspace_path
    ws_dir = get_project_workspace_path(project.name, str(project.id), project.workspace_path)
    ws_dir.mkdir(parents=True, exist_ok=True)

    cmd = req.command.strip()
    if not cmd:
        return {"command": "", "stdout": "", "stderr": "No command provided", "exit_code": 1}

    start_time = time.time()
    try:
        res = subprocess.run(
            cmd,
            shell=True,
            cwd=str(ws_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )
        duration = round(time.time() - start_time, 3)
        return {
            "command": cmd,
            "stdout": res.stdout,
            "stderr": res.stderr,
            "exit_code": res.returncode,
            "duration": duration,
            "workspace": str(ws_dir)
        }
    except subprocess.TimeoutExpired:
        return {
            "command": cmd,
            "stdout": "",
            "stderr": "Command execution timed out after 30 seconds",
            "exit_code": 124,
            "duration": 30.0,
            "workspace": str(ws_dir)
        }
    except Exception as e:
        return {
            "command": cmd,
            "stdout": "",
            "stderr": str(e),
            "exit_code": 1,
            "duration": 0.0,
            "workspace": str(ws_dir)
        }


@router.get("/projects/{project_id}/agent-traces", summary="Get agent reasoning chains and dedicated outputs")
async def get_agent_traces(
    project_id: str,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Return structured chain-of-thought and output deliverables for each agent."""
    import json
    from pathlib import Path

    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

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
                "count": len(traces)
            }
        except Exception as e:
            logger.warning("Failed to parse trace file", exc=str(e))

    return {
        "project_id": str(project_id),
        "workspace": str(ws_dir),
        "traces": [],
        "count": 0,
        "message": "No agent traces generated yet. Run the project to trigger autonomous reasoning."
    }


# === HERMES CONVERSATIONAL COPILOT & WORKSPACE FILES ENDPOINTS ===

class ProjectMessageCreate(BaseModel):
    content: str


@router.get("/projects/{project_id}/messages", summary="Get conversational messages with Hermes agent")
async def get_project_messages(
    project_id: str,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Retrieve chat history with Hermes agent, initializing interview if empty."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    from app.services.hermes_agent import HermesAgentService
    messages = await HermesAgentService.get_or_create_initial_messages(db_session, project)
    return {"project_id": str(project_id), "messages": messages}


@router.post("/projects/{project_id}/messages", summary="Send message to Hermes agent")
async def send_project_message(
    project_id: str,
    payload: ProjectMessageCreate,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Send user input to Hermes, receive guidance, and trigger execution if requested."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not payload.content.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty")

    from app.services.hermes_agent import HermesAgentService
    result = await HermesAgentService.handle_user_message(db_session, project, payload.content)

    # If user confirmed or triggered build, schedule the squad execution
    if result.get("trigger_build"):
        try:
            await trigger_project_run(project_id, db_session)
        except Exception as e:
            pass

    return result


@router.get("/projects/{project_id}/models", summary="Get model assignments and recommendations for squad")
async def get_project_models(
    project_id: str,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Get assigned and default free models for each role in the squad."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

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
    db_session: AsyncSession = Depends(get_db_session)
):
    """List all real code files and deliverables inside the project workspace directory."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

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
    return {"workspace": str(ws_dir), "files": files}


@router.get("/projects/{project_id}/files/content", summary="Get content of a file in workspace")
async def get_project_file_content(
    project_id: str,
    path: Optional[str] = None,
    file_path: Optional[str] = None,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Read full text content of a generated file in project workspace."""
    target_rel = path or file_path
    if not target_rel:
        raise HTTPException(status_code=400, detail="Path parameter is required")

    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    from app.services.workspace_helper import get_project_workspace_path
    ws_dir = get_project_workspace_path(project.name, str(project.id), project.workspace_path)

    target_file = (ws_dir / target_rel).resolve()
    if not str(target_file).startswith(str(ws_dir)) or not target_file.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        content = target_file.read_text(encoding="utf-8")
        return {"path": path, "content": content, "size": target_file.stat().st_size}
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Binary file cannot be viewed as text")



# === TASK ENDPOINTS ===

@router.post("/projects/{project_id}/tasks", response_model=TaskResponse, status_code=201, summary="Create task under project")
@router.post("/tasks", response_model=TaskResponse, status_code=201, summary="Create a new task")
async def create_task(
    task_in: TaskCreate,
    project_id: Optional[str] = None,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Create a new task."""
    if not task_in.title.strip():
        raise HTTPException(status_code=400, detail="Task title is required")

    effective_project_id = project_id or task_in.project_id
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
    db_session: AsyncSession = Depends(get_db_session)
):
    """Get task details."""
    task = await get_task(db_session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@router.get("/tasks", response_model=List[TaskResponse], summary="List all tasks")
async def list_all_tasks(
    db_session: AsyncSession = Depends(get_db_session)
):
    """List all tasks across all projects."""
    result = await db_session.execute(select(Task).order_by(Task.created_at.desc()))
    tasks = result.scalars().all()
    return [task.to_dict() for task in tasks]


@router.put("/tasks/{task_id}", response_model=TaskResponse, summary="Update task")
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
    db_session: AsyncSession = Depends(get_db_session)
):
    """Delete a task."""
    task = await get_task(db_session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await db_session.delete(task)
    await db_session.commit()
    return JSONResponse(
        status_code=200,
        content={"status": "success", "message": "Task deleted successfully", "id": task_id}
    )