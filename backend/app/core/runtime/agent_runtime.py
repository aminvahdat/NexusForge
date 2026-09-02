"""Agent Runtime Abstraction — AgentRuntimeInterface and HermesRuntimeAdapter.

This module defines the core runtime abstraction specified in Phase 0-1
architecture (docs/AGENT_ARCHITECTURE.md) and discovered during Phase 4B
Hermes inspection (docs/HERMES_INTEGRATION.md).

Critical invariant (from Phase 1 architecture):
    Agent Role = logical expertise profile (not a process)
    Worker = reusable execution resource (not tied to a single role)
    Hermes = runtime implementation behind AgentRuntimeInterface
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import json
from datetime import datetime, timezone
from typing import Optional, AsyncIterator, Dict, Any, List
from pathlib import Path
from enum import Enum

import structlog
from pydantic import BaseModel, Field

from app.config.settings import get_settings
from app.models.task import Task
from app.models.enums import AgentRole, TaskStatus, Priority

logger = structlog.get_logger()


# ── Status / Error Types ────────────────────────────────────────────────────

class Status(str, Enum):
    """Worker/Session statuses."""
    OFFLINE = "offline"
    IDLE = "idle"
    STARTING = "starting"
    THINKING = "thinking"
    RESEARCHING = "researching"
    RUNNING = "working"
    WAITING = "waiting"
    BLOCKED = "blocked"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPING = "stopping"


class RuntimeError(Exception):
    """Base exception for runtime errors."""
    pass


class SessionNotFound(RuntimeError):
    """Requested session does not exist."""
    pass


class ExecutionError(RuntimeError):
    """Execution failed (timeout, crash, error)."""
    pass


# ── Execution Context (Phase 4H) ────────────────────────────────────────────

class ExecutionContext(BaseModel):
    """Structured execution context — minimized to task-relevant info only.
    Phase 4H: Context Packaging (minimized context, not full DB/project)."""

    project_id: Optional[str] = None
    task: Optional[Task] = None
    role: Optional[AgentRole] = None
    requirements: List[str] = Field(default_factory=list)
    relevant_artifacts: List[str] = Field(default_factory=list)
    relevant_previous_results: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    allowed_tools: List[str] = Field(default_factory=lambda: [
        "terminal", "coding", "file", "project", "skills"
    ])
    allowed_skills: List[str] = Field(default_factory=list)
    workspace_path: Optional[str] = None
    approval_policy: str = "smart"  # smart / manual / off
    memory_context: Optional[Dict[str, Any]] = None
    max_execution_time: Optional[int] = 180  # seconds (timeout)
    max_output_size: int = 1024 * 1024  # 1MB output limit

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


# ── Session / Event Types ───────────────────────────────────────────────────

class SessionResult(BaseModel):
    """Result of a session execution (Phase 4L: Events)."""

    session_id: str
    task_id: Optional[str] = None
    status: Status = Status.IDLE
    output: Optional[str] = None
    artifacts: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_duration_sec: Optional[float] = None


class Event(BaseModel):
    """Normalized execution event (Phase 4L: Events model).
    Events include structured metadata — not parsed from log text."""

    event_type: str
    session_id: str
    task_id: Optional[str] = None
    worker_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ── Agent Runtime Interface (Phase 4C) ──────────────────────────────────────

class AgentRuntimeInterface:
    """Abstract runtime interface for agent execution.

    Defined in Phase 0-1 architecture (AGENT_ARCHITECTURE.md):
        The interface abstracts runtime implementations (Hermes, OpenAI,
        Anthropic, local models) so the orchestration layer doesn't depend
        on any specific runtime.
    """

    def initialize(self) -> None:
        """Initialize runtime (verify binary, load adapter settings)."""
        raise NotImplementedError

    def assign_role(
        self,
        session_id: str,
        role: AgentRole,
        context: ExecutionContext,
    ) -> None:
        """Assign a logical agent role profile to a session."""
        raise NotImplementedError

    def execute_task(
        self,
        session_id: str,
        context: ExecutionContext,
    ) -> SessionResult:
        """Start execution. Returns result synchronously or via stream."""
        raise NotImplementedError

    async def stream_events(
        self, session_id: str
    ) -> AsyncIterator[Event]:
        """Stream execution events (Phase 4L)."""
        raise NotImplementedError

    def cancel(self, session_id: str) -> None:
        """Cancel running execution (Phase 4K: cancellation)."""
        raise NotImplementedError

    def get_status(self, session_id: str) -> Status:
        """Get session status."""
        raise NotImplementedError

    def terminate(self, session_id: str) -> None:
        """Force terminate session (Phase 4K: termination)."""
        raise NotImplementedError

    def shutdown(self) -> None:
        """Clean up all active sessions."""
        raise NotImplementedError

    def create_session(self, context: ExecutionContext) -> str:
        """Create a new session (isolation: workspace + session registry)."""
        raise NotImplementedError


# ── Hermes Runtime Adapter (Phase 4B discovery → implementation) ─────────────

class HermesRuntimeAdapter(AgentRuntimeInterface):
    """Hermes adapter discovered during Phase 4B inspection.

    Key findings (docs/HERMES_INTEGRATION.md):
        - Hermes is CLI-based (`/home/yellowdeerco/.local/bin/hermes`)
        - One-shot mode: `hermes -z "PROMPT"`
        - Isolation: `hermes --worktree -w`
        - Tools: `-t terminal,code_execution,coding,file,project,skills`
        - No direct Python AgentRuntimeInterface — adapter uses subprocess
        - Session management: `hermes --resume SESSION`, `hermes sessions`
        - Memory: `hermes memory setup`
        - Skills: `hermes skills`
        - MCP: `hermes mcp`

    This adapter bridges the abstract AgentRuntimeInterface and the actual
    Hermes CLI, maintaining full isolation and security controls.
    """

    def __init__(self, settings: Optional[Any] = None):
        self.settings = settings or get_settings()
        self.session_registry: Dict[str, Dict[str, Any]] = {}
        self.default_toolsets: str = (
            "terminal,code_execution,coding,file,project,skills"
        )
        # Security: default approval mode is "smart" (not --yolo = no bypass)
        self.default_approval = "smart"

    def initialize(self) -> None:
        """Verify Hermes binary and version."""
        hermes_path = "/home/yellowdeerco/.local/bin/hermes"
        if not Path(hermes_path).exists():
            # Try system path
            result = subprocess.run(
                ["which", "hermes"], capture_output=True, text=True
            )
            hermes_path = result.stdout.strip() if result.returncode == 0 else "hermes"
        try:
            result = subprocess.run(
                [hermes_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            logger.info(
                "hermes_adapter.initialized",
                version=result.stdout.strip()[:50],
                hermes_path=hermes_path,
            )
        except Exception as exc:
            logger.error(
                "hermes_adapter.init_failed",
                error=str(exc),
            )
            # Don't raise — adapter can work without version verification
            # (matches graceful degradation design from Phase 1 architecture)

    def create_session(
        self, context: ExecutionContext
    ) -> str:
        """Create isolated session with workspace isolation.

        Uses `hermes --worktree -w` for isolation (Phase 4I: Workspace Isolation).
        Workspace path: /workspaces/<project-id>/ (not host filesystem access).
        """
        session_id = (
            f"sess_{context.project_id or 'no_project'}_"
            f"{context.role.value if context.role else 'unknown'}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        workspace = (
            context.workspace_path
            or f"/workspaces/{context.project_id or 'global'}"
        )

        # Ensure workspace exists but is isolated
        workspace_path = Path(workspace)
        workspace_path.mkdir(parents=True, exist_ok=True)

        # Security: workspace isolation check (Phase 4I)
        # Ensure workspace is within allowed directory (prevent path traversal)
        allowed_base = Path("/workspaces")
        resolved = workspace_path.resolve()
        try:
            resolved.relative_to(allowed_base.resolve())
        except ValueError as exc:
            raise RuntimeError(
                f"Workspace isolation violation: {workspace} escapes allowed base"
            ) from exc

        self.session_registry[session_id] = {
            "context": context,
            "workspace": workspace,
            "status": Status.IDLE,
            "created_at": datetime.now(timezone.utc),
        }
        logger.info(
            "session.created",
            session_id=session_id,
            workspace=str(workspace_path),
            role=context.role.value if context.role else "generalist",
        )
        return session_id

    def assign_role(
        self,
        session_id: str,
        role: AgentRole,
        context: ExecutionContext,
    ) -> None:
        """Assign logical role profile to session (Phase 4D: Role System).

        Role = logical profile, not a process. The adapter updates the
        session registry; the actual execution uses the role profile for
        prompt construction and tool selection.
        """
        if session_id not in self.session_registry:
            raise SessionNotFound(session_id)
        self.session_registry[session_id]["context"].role = role
        logger.info(
            "session.role_assigned",
            session_id=session_id,
            role=role.value,
        )

    def execute_task(
        self,
        session_id: str,
        context: ExecutionContext,
    ) -> SessionResult:
        """Execute task using Hermes CLI adapter.

        Uses subprocess invocation (`subprocess.run`) for isolation,
        matching Phase 4B Hermes discovery.
        """
        if session_id not in self.session_registry:
            raise SessionNotFound(session_id)
        session_data = self.session_registry[session_id]
        session_data["status"] = Status.RUNNING

        workspace_path = session_data.get("workspace", "/workspaces/global")
        role_name = (
            context.role.value if context.role else AgentRole.CHIEF_ORCHESTRATOR.value
        )

        # Build minimized prompt from ExecutionContext (Phase 4H)
        prompt_parts = [
            f"You are a {role_name.replace('_', ' ').title()} agent.",
            f"Project: {context.project_id or 'N/A'}",
            f"Task: {context.task.title if context.task else 'Unknown'}",
        ]
        if context.task and context.task.description:
            prompt_parts.append(f"Task description: {context.task.description}")
        if context.allowed_tools:
            prompt_parts.append(
                f"Allowed tools: {', '.join(context.allowed_tools)}"
            )
        if context.approval_policy:
            prompt_parts.append(
                f"Approval policy: {context.approval_policy}"
            )
        # Security: never include API keys, tokens, or secrets in prompt
        prompt = "\n".join(prompt_parts)

        # Build hermes CLI command
        hermes_path = "/home/yellowdeerco/.local/bin/hermes"
        cmd = [
            hermes_path,
            "-z", prompt,
            "-t", ",".join(context.allowed_tools or self.default_toolsets.split(",")),
        ]
        # Add worktree isolation (Phase 4I: isolation)
        cmd.extend(["--worktree", "-w"])

        # Security: no shell=True (prevents command injection)
        # Security: cwd is workspace path (Phase 4I: filesystem isolation)

        logger.info(
            "execution.started",
            session_id=session_id,
            command=f"hermes -z ... -t ... --worktree",
            workspace=str(workspace_path),
            role=role_name,
        )

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(workspace_path),
                timeout=context.max_execution_time or 180,
            )
        except subprocess.TimeoutExpired as exc:
            session_data["status"] = Status.FAILED
            logger.error(
                "execution.timeout",
                session_id=session_id,
                max_time=context.max_execution_time,
            )
            return SessionResult(
                session_id=session_id,
                status=Status.FAILED,
                error=f"Execution timeout after {context.max_execution_time}s",
                started_at=session_data.get("created_at"),
                completed_at=datetime.now(timezone.utc),
            )
        except Exception as exc:
            session_data["status"] = Status.FAILED
            logger.error("execution.error", session_id=session_id, error=str(exc))
            return SessionResult(
                session_id=session_id,
                status=Status.FAILED,
                error=str(exc),
                started_at=session_data.get("created_at"),
                completed_at=datetime.now(timezone.utc),
            )

        # Process results
        output_text = result.stdout if result.returncode == 0 else result.stderr or result.stdout
        # Truncate output to max_output_size
        if len(output_text) > (context.max_output_size or 1024 * 1024):
            output_text = output_text[:context.max_output_size or 1024 * 1024]
            output_text += "\n... [output truncated due to size limit]"

        # Extract artifacts from workspace (Phase 4M)
        artifacts = []
        workspace_path_obj = Path(workspace_path)
        artifacts_dir = workspace_path_obj / "artifacts"
        if artifacts_dir.exists():
            artifacts = [str(p.name) for p in artifacts_dir.iterdir() if p.is_file()]

        session_data["status"] = Status.COMPLETED if result.returncode == 0 else Status.FAILED
        completed_at = datetime.now(timezone.utc)
        started_at = session_data.get("created_at")
        duration = (completed_at - started_at).total_seconds() if started_at else None

        result_obj = SessionResult(
            session_id=session_id,
            task_id=context.task.id if context.task else None,
            status=Status.COMPLETED if result.returncode == 0 else Status.FAILED,
            output=output_text,
            artifacts=artifacts,
            error=result.stderr if result.returncode != 0 else None,
            started_at=started_at,
            completed_at=completed_at,
            execution_duration_sec=duration,
        )

        logger.info(
            "execution.completed",
            session_id=session_id,
            status=result_obj.status.value,
            duration_sec=duration,
            artifacts=len(artifacts),
            error=bool(result.returncode != 0),
        )
        return result_obj

    async def stream_events(
        self, session_id: str
    ) -> AsyncIterator[Event]:
        """Stream execution events.

        For Phase 4, this is a minimal implementation: yields events from
        session state changes (start, work, complete, fail). In production,
        it would poll `hermes sessions browse` or read a file descriptor.
        Phase 4L: Events must contain structured metadata (not log parsing).
        """
        session_data = self.session_registry.get(session_id)
        if not session_data:
            raise SessionNotFound(session_id)

        # Yield start event
        yield Event(
            event_type="WORKER_ASSIGNED",
            session_id=session_id,
            task_id=session_data.get("context", ExecutionContext()).task.id if session_data.get("context", ExecutionContext()).task else None,
            timestamp=datetime.now(timezone.utc),
            metadata={
                "workspace": session_data.get("workspace"),
                "status": session_data.get("status", Status.IDLE).value,
            },
        )
        # Yield work events
        yield Event(
            event_type="WORKER_WORKING",
            session_id=session_id,
            task_id=session_data.get("context", ExecutionContext()).task.id if session_data.get("context", ExecutionContext()).task else None,
            timestamp=datetime.now(timezone.utc),
            metadata={"status": session_data.get("status", Status.IDLE).value},
        )
        # Yield completion event
        yield Event(
            event_type="TASK_COMPLETED",
            session_id=session_id,
            timestamp=datetime.now(timezone.utc),
            metadata={"status": session_data.get("status", Status.IDLE).value},
        )

    def cancel(self, session_id: str) -> None:
        """Cancel running session (Phase 4K: cancellation)."""
        session_data = self.session_registry.get(session_id)
        if not session_data:
            raise SessionNotFound(session_id)
        # For subprocess-based adapter: terminate the process
        # The adapter stores process info; for this minimal version,
        # we change state and indicate process should terminate
        session_data["status"] = Status.STOPPING
        logger.info("session.cancelled", session_id=session_id)

    def get_status(self, session_id: str) -> Status:
        session_data = self.session_registry.get(session_id)
        if not session_data:
            raise SessionNotFound(session_id)
        return Status(session_data.get("status", Status.IDLE))

    def terminate(self, session_id: str) -> None:
        """Force terminate session (Phase 4K: termination)."""
        session_data = self.session_registry.get(session_id)
        if not session_data:
            raise SessionNotFound(session_id)
        session_data["status"] = Status.OFFLINE
        # In production, kill subprocess; clean workspace (preserve artifacts)
        logger.info("session.terminated", session_id=session_id)

    def shutdown(self) -> None:
        """Clean up all active sessions."""
        for sid in list(self.session_registry.keys()):
            try:
                self.terminate(sid)
            except Exception:
                pass
        logger.info("runtime.shutdown", active_sessions=len(self.session_registry))


# ── Convenience Function ────────────────────────────────────────────────────

def get_adapter() -> AgentRuntimeInterface:
    """Get configured adapter instance.
    Phase 0-1 design: adapter is injectable; future adapters
    (OpenAI, Anthropic, local) can be added without redesigning orchestration.
    """
    return HermesRuntimeAdapter()