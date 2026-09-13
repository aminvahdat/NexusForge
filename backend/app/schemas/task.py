"""Pydantic schemas for NexusForge tasks."""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Any
from datetime import datetime
from app.models import Task as TaskModel
from app.models.enums import AgentRole, Priority, TaskStatus


class TaskBase(BaseModel):
    """Base task schema with common fields."""

    title: str = Field(..., max_length=500, description="Task title")
    description: str = Field(..., description="Detailed task description")
    role: Optional[str] = Field(default="chief_orchestrator", description="Agent role assigned to this task")
    required_skills: List[str] = Field(default_factory=list, description="Required agent skills")
    dependencies: List[str] = Field(default_factory=list, description="Task dependency IDs")
    input_artifacts: List[Any] = Field(default_factory=list, description="Input artifact IDs or objects")
    output_artifacts: List[Any] = Field(default_factory=list, description="Output artifact IDs or objects")
    acceptance_criteria: List[Any] = Field(default_factory=list, description="Acceptance criteria")

    class Config:
        from_attributes = True


class TaskCreate(TaskBase):
    """Schema for creating a task."""

    task_id: Optional[str] = Field(None, description="Custom task ID (optional)")
    project_id: Optional[str] = Field(None, description="Project ID")
    priority: str = Field(default=Priority.MEDIUM.value, description="Task priority")
    status: str = Field(default=TaskStatus.QUEUED.value, description="Initial task status")
    retry_count: int = Field(default=0, ge=0, description="Current retry count")
    max_retries: int = Field(default=3, ge=0, description="Maximum retries")
    due_date: Optional[datetime] = Field(None, description="Optional due date")


class TaskUpdate(BaseModel):
    """Schema for updating a task."""

    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    role: Optional[str] = None
    required_skills: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    input_artifacts: Optional[List[Any]] = None
    output_artifacts: Optional[List[Any]] = None
    acceptance_criteria: Optional[List[Any]] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_worker: Optional[str] = None
    retry_count: Optional[int] = Field(None, ge=0)
    max_retries: Optional[int] = Field(None, ge=0)
    due_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskResponse(TaskBase):
    """Schema for task responses."""

    id: str = Field(..., description="Task ID (UUID)")
    task_id: Optional[str] = Field(None, description="Business task ID")
    project_id: str = Field(..., description="Project ID")
    status: str = Field(..., description="Task status")
    priority: str = Field(..., description="Task priority")
    assignment_id: Optional[str] = Field(None, description="Assignment identifier")
    assigned_worker: Optional[str] = Field(None, description="Worker ID")
    retry_count: int = Field(..., ge=0)
    max_retries: int = Field(..., ge=0)
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output_artifacts: List[Any] = Field(default_factory=list)
    error: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    estimated_tokens: Optional[int] = None


def task_from_model(model: TaskModel) -> TaskResponse:
    """Convert a Task model to a TaskResponse."""
    return TaskResponse(
        id=str(model.id),
        task_id=model.task_id,
        project_id=str(model.project_id),
        title=model.title,
        description=model.description,
        role=model.role,
        required_skills=model.required_skills,
        dependencies=model.dependencies,
        input_artifacts=model.input_artifacts,
        output_artifacts=model.output_artifacts,
        acceptance_criteria=model.acceptance_criteria,
        priority=model.priority,
        status=model.status,
        assigned_worker=model.assigned_worker,
        retry_count=model.retry_count,
        max_retries=model.max_retries,
        due_date=model.due_date,
        created_at=model.created_at,
        updated_at=model.updated_at,
        started_at=model.started_at,
        completed_at=model.completed_at,
        metadata=model.metadata,
        estimated_tokens=model.estimated_tokens,
    )
