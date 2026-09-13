"""Artifact management API routes for viewing, inspecting, and managing project artifacts.

Hardened with authentication, project ownership validation, and path traversal protection.
"""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db import get_db_session
from app.models import Artifact, Project, Task, User
from app.schemas.artifact import ArtifactResponse, ArtifactCreate, ArtifactUpdate
from app.auth import get_current_user
from app.authorization import enforce_ownership
from app.services.database import get_project, get_task
from app.services.workspace_helper import get_project_workspace_path

router = APIRouter(prefix="/artifacts", tags=["artifact", "management"])


def to_uuid(val) -> Optional[uuid.UUID]:
    if val is None or isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except (ValueError, AttributeError):
        return None


@router.get("/project/{project_id}", summary="List artifacts for project")
async def list_project_artifacts(
    project_id: str,
    artifact_type: Optional[str] = None,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """List all artifacts tied to a project with ownership verification."""
    project = await get_project(db_session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    enforce_ownership(project.owner_id, current_user, "project")

    p_uuid = to_uuid(project_id) or project.id
    conditions = [Artifact.project_id == p_uuid]
    if artifact_type:
        conditions.append(Artifact.type == artifact_type)

    result = await db_session.execute(
        select(Artifact).where(and_(*conditions)).order_by(Artifact.created_at.desc())
    )
    artifacts = result.scalars().all()
    return [art.to_dict() for art in artifacts]


@router.get("/task/{task_id}", summary="List artifacts for task")
async def list_task_artifacts(
    task_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """List artifacts associated with a specific task with ownership verification."""
    task = await get_task(db_session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.project_id:
        project = await get_project(db_session, str(task.project_id))
        if project:
            enforce_ownership(project.owner_id, current_user, "task")

    t_uuid = to_uuid(task_id) or task.id
    result = await db_session.execute(
        select(Artifact).where(Artifact.task_id == t_uuid).order_by(Artifact.created_at.desc())
    )
    artifacts = result.scalars().all()
    return [art.to_dict() for art in artifacts]


@router.get("/{artifact_id}", summary="Get artifact details")
async def get_artifact(
    artifact_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Get full details of a single artifact with ownership verification."""
    a_uuid = to_uuid(artifact_id)
    if not a_uuid:
        raise HTTPException(status_code=404, detail="Artifact not found")

    result = await db_session.execute(select(Artifact).where(Artifact.id == a_uuid))
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    project = await get_project(db_session, str(artifact.project_id))
    if project:
        enforce_ownership(project.owner_id, current_user, "artifact")

    return artifact.to_dict()


@router.get("/{artifact_id}/content", summary="Read content of artifact file")
async def get_artifact_content(
    artifact_id: str,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """Read the text content of a generated artifact safely within workspace boundaries."""
    a_uuid = to_uuid(artifact_id)
    if not a_uuid:
        raise HTTPException(status_code=404, detail="Artifact not found")

    result = await db_session.execute(select(Artifact).where(Artifact.id == a_uuid))
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    project = await get_project(db_session, str(artifact.project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Associated project not found")

    enforce_ownership(project.owner_id, current_user, "artifact")

    ws_dir = get_project_workspace_path(project.name, str(project.id), project.workspace_path)
    ws_resolved = ws_dir.resolve()

    file_path = Path(artifact.path).resolve()

    # Path traversal validation: file must reside within project workspace
    if not file_path.is_relative_to(ws_resolved):
        raise HTTPException(status_code=403, detail="Access denied: Artifact file outside workspace boundary")

    if not file_path.exists() or not file_path.is_file():
        return {
            "id": str(artifact.id),
            "name": artifact.name,
            "type": artifact.type,
            "path": str(artifact.path),
            "content": artifact.description or "No file content available on disk."
        }

    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Binary file cannot be viewed as text")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read artifact file: {e}")

    return {
        "id": str(artifact.id),
        "name": artifact.name,
        "type": artifact.type,
        "path": str(artifact.path),
        "content": content
    }