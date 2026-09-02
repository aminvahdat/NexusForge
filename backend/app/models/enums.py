"""Enums and constants for NexusForge."""

from enum import Enum


class TaskStatus(str, Enum):
    """Task execution statuses."""
    QUEUED = "queued"
    PLANNING = "planning"
    BLOCKED = "blocked"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    REVIEWING = "reviewing"
    NEEDS_REVISION = "needs_revision"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRole(str, Enum):
    """Built-in logical agent roles."""
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
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WorkerStatus(str, Enum):
    """Worker operational statuses."""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class PermissionLevel(str, Enum):
    """Agent tool permission levels."""
    SAFE = "safe"          # Read-only: files, docs, search
    LIMITED = "limited"   # Write files, run tests, install approved deps
    PRIVILEGED = "privileged"  # Deploy, infra config
    DANGEROUS = "dangerous"  # Destructive ops — requires human approval


class RiskLevel(str, Enum):
    """Risk levels for approval requests."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
