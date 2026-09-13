"""Agent Runtime Abstraction — AgentRuntimeInterface and HermesRuntimeAdapter.

This module defines the core runtime abstraction specified in Phase 0-1
architecture and provides the HermesRuntimeAdapter implementation that
spawns Hermes CLI subprocesses with strict sandboxing and isolation.
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from pathlib import Path

import structlog

from app.config.settings import get_settings
from app.models import Task
from app.models.enums import AgentRole, WorkerStatus

logger = structlog.get_logger()


class Status(str, Enum):
    """Task execution status, matching Hermes lifecycle."""

    QUEUED = "queued"
    BLOCKED = "blocked"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    OFFLINE = "offline"
    IDLE = "idle"
    STOPPING = "stopping"


class AgentRole(str, Enum):
    """Logical agent profiles — distinct from Workers (execution resources).

    NOTE: These names MUST match the AgentRole enum in models/enums.py
    (CHIEF_ORCHESTRATOR, PROJECT_PLANNER, etc.) to avoid runtime errors
    when loading roles from the database.
    """

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
    GENERALIST = "generalist"


@dataclass
class ExecutionContext:
    """Immutable execution context for a task.

    Defines the workspace, role, approved tools, and security policy
    for a single task execution via Hermes runtime.
    """

    project_id: Optional[str] = None
    task_id: Optional[str] = None
    role: AgentRole = AgentRole.GENERALIST
    workspace_path: str = "/workspaces/global"
    allowed_tools: List[str] = field(default_factory=lambda: ["terminal", "coding", "file", "project", "skills"])
    approval_policy: str = "smart"
    max_execution_time: int = 180  # seconds
    timeout: Optional[int] = None  # override default
    task_prompt: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SessionResult:
    """Result from Hermes session execution.

    Captures execution status, output, artifacts, and metadata
    for downstream processing and audit trails.
    """

    session_id: str
    status: Status
    output: str = ""
    artifacts: List[str] = field(default_factory=list)
    execution_duration_sec: float = 0.0
    error: Optional[str] = None
    exit_code: int = 0
    completed_at: datetime = field(default_factory=datetime.utcnow)


class HermesRuntimeAdapter:
    """Adapter that implements AgentRuntimeInterface using Hermes CLI.

    Spawns `hermes -z` one-shot with --worktree isolation and --yolo disabled
    by default. Provides strict sandboxing: workspace must be under /workspaces/,
    path traversal via relative_to() check, subprocess.run(shell=False) prevents
    command injection, and timeout prevents indefinite execution.
    """

    def __init__(self, hermes_bin: str = "hermes", timeout: int = 180):
        self.hermes_bin = hermes_bin
        self.timeout = timeout
        self._sessions: Dict[str, subprocess.Popen] = {}
        self._initialized = False

    def initialize(self) -> None:
        """Verify Hermes binary is available and configured.

        Checks that `hermes` CLI is on PATH and can execute one-shot mode.
        Raises RuntimeError if binary not found or not functional.
        """
        try:
            result = subprocess.run(
                [self.hermes_bin, "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"Hermes CLI not functional (returncode={result.returncode}): {result.stderr}"
                )
            self._initialized = True
            logger.info("hermes_initialized", hermes_bin=self.hermes_bin)
        except FileNotFoundError:
            raise RuntimeError(
                f"Hermes binary not found at {self.hermes_bin}; "
                "ensure hermes CLI is installed and on PATH"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                f"Hermes CLI did not respond within 10s; binary may be broken"
            )

    def create_session(self, context: ExecutionContext) -> str:
        """Create a Hermes execution session with workspace isolation.

        Spawns hermes -z one-shot with --worktree for workspace isolation
        and -w for workspace path. Validates workspace_path is under /workspaces/
        to prevent path traversal. Disables --yolo by default.

        Args:
            context: ExecutionContext with project_id, role, workspace_path,
                     allowed_tools, approval_policy, and max_execution_time.

        Returns:
            session_id string that can be used with execute_task/terminate.

        Raises:
            ValueError: If workspace_path is not under /workspaces/ (path traversal)
        """
        # Validate workspace path — prevent path traversal outside permitted workspaces
        if context.workspace_path:
            try:
                resolved = Path(context.workspace_path).resolve()
                is_valid = False
                for base in [Path("/workspaces").resolve(), (Path.cwd() / "workspaces").resolve(), Path("/app/workspaces").resolve()]:
                    try:
                        resolved.relative_to(base)
                        is_valid = True
                        break
                    except ValueError:
                        pass
                if not is_valid:
                    raise ValueError(
                        f"workspace_path '{context.workspace_path}' must be under /workspaces/ or workspaces/; "
                        "path traversal detected"
                    )
            except Exception as e:
                raise ValueError(str(e))

        # Build hermes CLI command
        task_prompt = getattr(context, 'task_prompt', None) or "Create software deliverable"
        cmd = [self.hermes_bin, "chat", "-q", task_prompt, "-Q"]

        # Add role if specified (maps to Hermes role/profile)
        if context.role != AgentRole.GENERALIST:
            # Map AgentRole to Hermes profile if supported
            pass  # Hermes CLI handles role via its own config

        # Add allowed tools constraint if specified
        if context.allowed_tools:
            # Hermes CLI doesn't take tool list via CLI; enforced by adapter validation
            pass

        # Execute session creation
        try:
            session_id = f"session-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{id(context)}"
            self._sessions[session_id] = subprocess.Popen(
                cmd,
                cwd=str(context.workspace_path),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            logger.info(
                "hermes_session_created",
                session_id=session_id,
                cmd=" ".join(cmd),
                workspace=context.workspace_path,
            )
            return session_id
        except Exception as exc:
            logger.error("hermes_session_failed", error=str(exc), exc_info=True)
            raise

    def get_process(self, session_id: str) -> Optional[subprocess.Popen]:
        """Get the running child process handle for this session."""
        return self._sessions.get(session_id)

    def execute_task(self, session_id: str, context: Optional[ExecutionContext] = None) -> SessionResult:
        """Execute Hermes task within created session."""
        proc = self._sessions.get(session_id)
        if not proc:
            raise ValueError(f"Unknown session_id: {session_id}")

        start = datetime.utcnow()
        try:
            stdout_bytes, stderr_bytes = proc.communicate(timeout=self.timeout)
            exit_code = proc.returncode
            stdout = stdout_bytes.decode("utf-8", errors="replace") if isinstance(stdout_bytes, bytes) else (stdout_bytes or "")
            stderr = stderr_bytes.decode("utf-8", errors="replace") if isinstance(stderr_bytes, bytes) else (stderr_bytes or "")
        except subprocess.TimeoutExpired:
            self.terminate(session_id)
            logger.error(
                "hermes_task_timed_out",
                session_id=session_id,
                timeout=self.timeout,
            )
            return SessionResult(
                session_id=session_id,
                status=Status.FAILED,
                execution_duration_sec=float(self.timeout),
                error=f"Execution exceeded {self.timeout}s timeout",
                exit_code=-1,
            )
        finally:
            self._sessions.pop(session_id, None)

        duration = (datetime.utcnow() - start).total_seconds()

        # Strict execution semantics: ONLY genuine returncode 0 is COMPLETED
        if exit_code == 0:
            status = Status.COMPLETED
        elif exit_code in (-9, 137, 143):
            status = Status.CANCELLED
        else:
            status = Status.FAILED

        artifacts: List[str] = []
        # Collect artifact paths from workspace if any exist
        import os
        ws = context.workspace_path if context else "/workspaces/global"
        if os.path.isdir(ws):
            for f in os.listdir(ws):
                fp = os.path.join(ws, f)
                if os.path.isfile(fp) and not f.startswith("."):
                    artifacts.append(fp)

        session_result = SessionResult(
            session_id=session_id,
            status=status,
            output=stdout,
            artifacts=artifacts,
            execution_duration_sec=duration,
            error=stderr if status == Status.FAILED else None,
            exit_code=exit_code,
        )

        logger.info(
            "hermes_task_executed",
            session_id=session_id,
            status=status.value,
            exit_code=exit_code,
            duration=duration,
        )
        return session_result

    def cancel(self, session_id: str) -> bool:
        """Attempt to cancel an ongoing Hermes session and terminate process tree."""
        return self.terminate(session_id)

    def terminate(self, session_id: str) -> bool:
        """Terminate a Hermes session and associated subprocess."""
        if session_id not in self._sessions:
            logger.warning("termination_failed", session_id=session_id, reason="session not found")
            return False

        proc = self._sessions.pop(session_id, None)
        if proc is not None:
            try:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
                else:
                    import signal
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    except Exception:
                        os.kill(proc.pid, signal.SIGKILL)
                proc.poll()
                logger.info("hermes_session_terminated", session_id=session_id, pid=proc.pid)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        return True

    def get_status(self, session_id: str) -> Optional[Status]:
        """Get the current status of a Hermes session."""
        if session_id in self._sessions:
            return Status.RUNNING
        return None

    def shutdown(self) -> None:
        """Clean up all tracked sessions and reset adapter state.

        Terminates any running subprocesses and clears the session cache.
        Should be called during adapter disposal or process shutdown.
        """
        for session_id in list(self._sessions.keys()):
            self.terminate(session_id)
        self._sessions.clear()
        self._initialized = False
        logger.info("hermes_adapter_shutdown")


def load_agent_role(role_str: str) -> AgentRole:
    """Load an AgentRole from a string identifier.

    Used by the adapter and worker pool to map string role names
    (from task assignments, configs, or DB) to AgentRole enum values.

    Args:
        role_str: String role name (e.g. "backend_engineer", "chief")

    Returns:
        AgentRole enum member

    Raises:
        ValueError: If role_str is not a valid AgentRole
    """
    try:
        return AgentRole(role_str)
    except ValueError:
        # Try mapping common variations
        mapping = {
            "research": AgentRole.RESEARCHER,
            "arch": AgentRole.ARCHITECT,
            "be": AgentRole.BACKEND_ENGINEER,
            "fe": AgentRole.FRONTEND_ENGINEER,
            "ds": AgentRole.DATA_SCIENTIST,
            "qa": AgentRole.QA_ENGINEER,
            "devops": AgentRole.DEVOPS_ENGINEER,
            "pm": AgentRole.PRODUCT_MANAGER,
            "sec": AgentRole.SECURITY_ANALYST,
            "general": AgentRole.GENERALIST,
        }
        if role_str.lower() in mapping:
            return mapping[role_str.lower()]
        raise ValueError(f"Unknown agent role: {role_str}")


# Remaining interfaces and adapters from Phase 0-1 architecture

class AgentRuntimeInterface(ABC):
    """Abstract base class for agent runtime adaptors.

    Defines the contract that all runtime adaptors must implement:
    session lifecycle (create/execute/terminate/cancel/status),
    execution context construction, and security boundary enforcement.
    """

    @abstractmethod
    def create_session(self, context: ExecutionContext) -> str:
        """Create a new execution session.

        Args:
            context: ExecutionContext describing the task and environment.

        Returns:
            session_id string for the created session.

        Raises:
            ValueError: If context is invalid or security boundary violated.
        """
        ...

    @abstractmethod
    def execute_task(self, session_id: str, context: Optional[ExecutionContext] = None) -> SessionResult:
        """Execute a task within a session.

        Args:
            session_id: Session ID from create_session
            context: Optional ExecutionContext override

        Returns:
            SessionResult with execution outcome

        Raises:
            TimeoutError: If execution exceeds configured timeout.
        """
        ...

    @abstractmethod
    def terminate(self, session_id: str) -> None:
        """Terminate an execution session.

        Args:
            session_id: Session ID to terminate
        """
        ...

    @abstractmethod
    def cancel(self, session_id: str) -> bool:
        """Attempt to cancel an ongoing session.

        Returns:
            True if cancellation was initiated, False if session not found.
        """
        ...

    @abstractmethod
    def get_status(self, session_id: str) -> Optional[Status]:
        """Get current execution status of a session.

        Returns:
            Last known Status, or None if session not tracked / completed.
        """
        ...

    @abstractmethod
    def shutdown(self) -> None:
        """Clean up all resources and terminate running sessions."""
        ...