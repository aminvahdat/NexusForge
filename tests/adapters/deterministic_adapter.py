"""Test-Only Deterministic Artifact Adapter.

FOR TEST INFRASTRUCTURE ONLY — NEVER IMPORT OR USE IN PRODUCTION RUNTIME.

Executes deterministic child processes in tests to verify process lifecycle,
workspace isolation boundaries, and cancellation signals without requiring
external LLM API tokens.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from uuid import uuid4

from backend.app.core.runtime.agent_runtime import (
    AgentRuntimeInterface,
    ExecutionContext,
    SessionResult,
    Status,
)


class DeterministicArtifactAdapter(AgentRuntimeInterface):
    """Test-only deterministic agent runtime adapter.

    Executes tasks deterministically inside a workspace using real OS child processes,
    producing verifiable files, recording genuine OS PIDs, and supporting real process
    tree termination for timeout and cancellation during test suite runs.
    """

    def __init__(self, should_fail: bool = False, delay: float = 0.0):
        self.should_fail = should_fail
        self.delay = delay
        self._active: Dict[str, ExecutionContext] = {}
        self._procs: Dict[str, subprocess.Popen] = {}

    def initialize(self) -> None:
        pass

    def create_session(self, context: ExecutionContext) -> str:
        resolved = Path(context.workspace_path).resolve()
        is_valid = False
        for base in [
            Path("/workspaces").resolve(),
            (Path.cwd() / "workspaces").resolve(),
            Path("/app/workspaces").resolve(),
        ]:
            try:
                resolved.relative_to(base)
                is_valid = True
                break
            except ValueError:
                pass
        if not is_valid:
            raise ValueError(
                f"workspace_path '{context.workspace_path}' violates workspace security boundary; path traversal detected"
            )

        sess_id = f"sess-det-{uuid4().hex[:8]}"
        self._active[sess_id] = context
        return sess_id

    def get_process(self, session_id: str) -> Optional[subprocess.Popen]:
        """Get the running child process handle for this test session."""
        return self._procs.get(session_id)

    def execute_task(self, session_id: str, context: Optional[ExecutionContext] = None) -> SessionResult:
        ctx = context or self._active.get(session_id)
        if not ctx:
            raise ValueError(f"Unknown session_id: {session_id}")

        workspace_path = Path(ctx.workspace_path)
        workspace_path.mkdir(parents=True, exist_ok=True)

        task_prompt = (getattr(ctx, "task_prompt", None) or "").lower()
        is_failure = self.should_fail or "[fail]" in task_prompt or "fail_test" in task_prompt
        is_sleep = "[long_running]" in task_prompt or "sleep" in task_prompt or self.delay > 0

        if is_failure:
            py_code = "import sys; sys.stderr.write('Deterministic execution failure\\n'); sys.exit(42)"
        elif is_sleep:
            sleep_duration = int(self.delay) if self.delay > 0 else 60
            py_code = f"import time; time.sleep({sleep_duration})"
        else:
            # Generate deterministic build manifest for test verification without artificial delays
            py_code = (
                "import json\n"
                "from pathlib import Path\n"
                "p = Path('build_manifest.json')\n"
                "p.write_text(json.dumps({'status': 'verified', 'generator': 'NexusForge Test Engine'}), encoding='utf-8')\n"
            )

        cmd = [sys.executable, "-c", py_code]
        start_time = datetime.utcnow()

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(workspace_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self._procs[session_id] = proc

            try:
                stdout, stderr = proc.communicate(timeout=180)
                exit_code = proc.returncode
            except subprocess.TimeoutExpired:
                self.terminate(session_id)
                return SessionResult(
                    session_id=session_id,
                    status=Status.FAILED,
                    exit_code=-1,
                    error="Execution timed out",
                )

            duration = (datetime.utcnow() - start_time).total_seconds()
            status = Status.COMPLETED if exit_code == 0 else Status.FAILED

            return SessionResult(
                session_id=session_id,
                status=status,
                exit_code=exit_code,
                output=stdout,
                error=stderr if exit_code != 0 else None,
                execution_duration_sec=duration,
            )
        finally:
            self._procs.pop(session_id, None)

    def terminate(self, session_id: str) -> None:
        self.cancel(session_id)

    def cancel(self, session_id: str) -> bool:
        proc = self._procs.pop(session_id, None)
        self._active.pop(session_id, None)
        if proc:
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
                return True
            except Exception:
                return False
        return True

    def get_status(self, session_id: str) -> Optional[Status]:
        if session_id in self._procs:
            return Status.RUNNING
        return Status.COMPLETED

    def shutdown(self) -> None:
        for sid in list(self._procs.keys()):
            self.cancel(sid)
        self._active.clear()
