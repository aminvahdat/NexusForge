from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    QUEUED = "queued"
    PLANNING = "planning"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    REVIEWING = "reviewing"
    NEEDS_REVISION = "needs_revision"
    CANCELLED = "cancelled"


class AgentRole(str, Enum):
    CHIEF_ORCHESTRATOR = "chief_orchestrator"
    PROJECT_PLANNER = "project_planner"
    SOFTWARE_ARCHITECT = "software_architect"
    RESEARCH_AGENT = "research_agent"
    UI_UX_AGENT = "ui_ux_agent"
    FRONTEND_AGENT = "frontend_agent"
    BACKEND_AGENT = "backend_agent"
    MOBILE_AGENT = "mobile_agent"
    DATABASE_AGENT = "database_agent"
    SECURITY_AGENT = "security_agent"
    QA_AGENT = "qa_agent"
    DEVOPS_AGENT = "devops_agent"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task(BaseModel):
    id: str = Field(default_factory=lambda: f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    title: str
    description: str
    role: AgentRole
    required_skills: List[str]
    dependencies: List[str] = []
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.QUEUED
    project_id: str
    assigned_worker: Optional[str] = None
    input_artifacts: List[str] = []
    output_artifacts: List[str] = []
    acceptance_criteria: List[str] = []
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    due_date: Optional[datetime] = None

    class Config:
        orm_mode = True
