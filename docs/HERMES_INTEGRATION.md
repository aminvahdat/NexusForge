# NexusForge — Hermes Integration

Based on inspection of the Hermes installation (`/home/yellowdeerco/.local/bin/hermes`) and the `hermes-agent` skill references (`cli-reference.md`, `configuration.md`, `SKILL.md`), the following integration architecture is documented.

## How Hermes Is Invoked

Hermes is a CLI tool invoked as subprocess:

```bash
# One-shot execution (for automated agent tasks)
hermes -z "Implement JWT authentication module" \
  --provider openrouter --model openrouter/free \
  -t terminal,code_execution,coding,file,project,skills

# With session resumption
hermes --resume SESSION_ID -t terminal,code_execution,coding

# Interactive
hermes chat -q "Analyze this code" -t web,browser,terminal
```

Key flags (from `cli-reference.md`):
- `-z, --oneshot PROMPT` — one-shot: print ONLY final response (for automation)
- `-m MODEL --provider P` — override model/provider for this invocation
- `-t TOOLSETS` — enable toolsets (terminal, file, coding, browser, etc.)
- `--skills SKILLS` — preload skills
- `--worktree, -w` — isolated git worktree mode (parallel agents, critical!)
- `--resume, -r SESSION` — resume session
- `--yolo` — skip dangerous command approval (NOT used by default — approval required!)

## Hermes Capabilities (Verified)

From `SKILL.md` and reference files:

| Capability | Status | Notes |
|-----------|--------|-------|
| **CLI invocation** | ✅ Verified | `hermes --help` works |
| **One-shot (`-z`)** | ✅ Verified | Non-interactive execution |
| **Tool execution** | ✅ Verified | Tools: terminal, file, coding, computer_use, browser, web, etc. |
| **Skills loading** | ✅ Verified | Skill system documented |
| **Memory (persistent)** | ✅ Verified | Memory provider, session store (`state.db`) |
| **Subagent/delegation** | ✅ Documented | `hermes moa`, delegation system |
| **MCP servers** | ✅ Verified | `hermes mcp add`, `hermes mcp serve` |
| **Gateway (platforms)** | ✅ Verified | Telegram, Discord, Slack, etc. |
| **Profile isolation** | ✅ Verified | `hermes profile create/use` |
| **Session management** | ✅ Verified | `hermes sessions list`, resume |
| **Web dashboard** | ✅ Verified | `hermes dashboard` |
| **Desktop app** | ✅ Verified | `hermes desktop` / `hermes gui` |

## What's NOT Directly Available (Requires Adapter)

Hermes does NOT expose a Python `AgentRuntimeInterface` natively. It is a CLI-driven agent framework. To integrate with NexusForge, we implement an adapter layer (`HermesRuntimeAdapter`) that:

1. Creates an isolated session (`hermes --worktree` for project isolation)
2. Passes execution context (task description, role, workspace path) via `-z` or interactive
3. Receives results via stdout/stderr (for `-z`) or session state (`hermes sessions export`)
4. Manages session lifecycle (create, resume, cancel, terminate)
5. Handles tool execution permissions (respecting approval settings)

## Integration Design (Agent Runtime Abstraction)

As defined in `docs/AGENT_ARCHITECTURE.md`:

```python
class AgentRuntimeInterface:
    def initialize(self): ...
    def assign_role(self, role: AgentRole, task: Task): ...
    def execute_task(self, task: Task, context: ExecutionContext): ...
    def stream_events(self) -> AsyncIterator[Event]: ...
    def cancel(self, session_id: str): ...
    def get_status(self, session_id: str) -> Status: ...
    def terminate(self, session_id: str): ...
    def shutdown(self): ...

class HermesRuntimeAdapter(AgentRuntimeInterface):
    def __init__(self):
        self.session_registry = {}
        self.default_toolsets = "terminal,code_execution,coding,file,project,skills"

    def initialize(self):
        # Verify hermes binary exists, check version
        pass

    def create_session(self, context: ExecutionContext) -> str:
        # Use `hermes --worktree -w` to create isolated workspace
        # Return session ID
        pass

    def execute_task(self, task: Task, context: ExecutionContext) -> SessionResult:
        # Build prompt from ExecutionContext (minimized context)
        # Call `hermes -z "$prompt" -t $toolsets --worktree`
        # Capture stdout/stderr, extract artifacts from workspace
        pass

    def stream_events(self) -> AsyncIterator[Event]:
        # Poll `hermes sessions browse` or read session state
        pass

    def cancel(self, session_id: str):
        # Send interrupt signal or call `hermes --resume` with cancellation
        pass

    def get_status(self, session_id: str) -> Status:
        # Check workspace, heartbeat, process status
        pass

    def terminate(self, session_id: str):
        # Kill process, clean workspace (except artifacts)
        pass

    def shutdown(self):
        # Terminate all active sessions
        pass
```

## Security Integration (Phase 4 Requirement)

The adapter must enforce:

1. **Workspace isolation**: Each session uses `--worktree` with isolated directory (`/workspaces/<project-id>/`)
2. **Path traversal prevention**: Workspace paths validated; `../` blocked; only allowed directories accessible
3. **Command permission model**: Tool execution gated by approval (DANGEROUS commands require approval unless `--yolo` explicitly set — and never by default)
4. **Secret handling**: Never pass secrets (API keys, tokens) to Hermes prompts; use environment injection for tools that need them
5. **Resource limits**: Execution timeout (`timeout=180` configured), max turns, output limits
6. **Log redaction**: Structured logging excludes secret content

## Session Lifecycle (Worker Pool Integration)

For Phase 4E (Worker Pool) and Phase 4F (Task Queue):

```python
# Worker starts (registers with Redis)
worker.register(worker_id="w-001", hostname="node-01", capabilities=[...])

# Scheduler picks task from Redis queue
# Selects worker with appropriate role profile

# Worker assigns role and creates session
session = adapter.create_session(context=ExecutionContext(
    project=project,
    task=task,
    role=AgentRole.BACKEND_ENGINEER,
    workspace=f"/workspaces/{project.id}",
    allowed_tools=["terminal", "coding", "file"],
    approval_policy="smart",  # Approvals for DANGEROUS commands
))

# Execute
result = adapter.execute_task(task, session, context)

# Events streamed back
for event in adapter.stream_events():
    # Persist to PostgreSQL (events table)
    # Publish to Redis pub/sub (for WebSocket frontend)
    # Log (structured, no secrets)
    pass

# On completion/failure/timeout: clean up or retry
adapter.terminate(session.id)  # Or preserve session for review
```

## Key Decisions (Documented)

1. **Hermes is CLI-based, not a Python library** — Adapter uses subprocess invocation (`subprocess.run` or `asyncio.create_subprocess_exec`)
2. **Agent Role ≠ Worker** — Role profile configured per task; worker dynamically loads it
3. **Isolation via `--worktree`** — Critical for security (prevents access to host filesystem)
4. **No `--yolo` by default** — All dangerous commands require approval (matches Phase 4J security requirements)
5. **Session state persisted** — Allows recovery after worker failure (Phase 4N failure handling)
6. **Events structured** — No parsing of human-readable log text (Phase 4L event system)

## References
- `docs/AGENT_ARCHITECTURE.md` — AgentRuntimeInterface definition
- `docs/WORKER_ARCHITECTURE.md` — Worker pool and lifecycle
- `docs/SECURITY_ARCHITECTURE.md` — Command permissions and approval model
- `backend/app/core/orchestration/chief.py` — ChiefOrchestrator (Phase 2 skeleton)
- `backend/app/services/redis.py` — Redis service (queue, heartbeat, session state)
