---
name: nexusforge-agent-runtime
description: "NexusForge agent runtime abstraction, Hermes adapter, secure worker execution, and workspace isolation. Use when implementing multi-agent orchestration with AgentRuntimeInterface, HermesRuntimeAdapter, worker pool (MAX_CONCURRENT_WORKERS=2), Redis task queue, role≠worker architecture, workspace isolation (--worktree), execution context minimization, event persistence, artifact management, and dangerous-command approval security."
version: 1.0.0
author: NexusForge Phase 4 Team
license: MIT
platforms: [linux, macos, windows]
metadata:
  category: autonomous-ai-agents
  tags: [nexusforge, agent-runtime, hermes-adapter, worker-pool, workspace-isolation, task-queue, event-system, artifact-management, security-approval]
  requires_hermes_skill: true
---

# NexusForge Agent Runtime

This skill captures the Phase 4 verification, audit, and architecture workflow: real Hermes runtime integration through `HermesRuntimeAdapter`, worker pool design (`WorkerPool`), task queue with atomic claiming (Redis `ZPOPMIN`), workspace isolation (`--worktree` + `relative_to` path check), event persistence, artifact collection, and dangerous-command approval security. It encodes the audit discipline (distinguish IMPLEMENTED vs PARTIAL vs NOT IMPLEMENTED; verify with executable evidence; document security findings; never claim E2E complete without `docs/PHASE4_E2E_RESULT.md`) and the runtime abstraction pattern (`AgentRuntimeInterface` → adapter, not direct Hermes coupling).

## When to Use This Skill

- Implementing or extending `AgentRuntimeInterface` / `HermesRuntimeAdapter`
- Building worker pool with `WorkerPool` service and Redis heartbeat (`WORKER_STATE` hash)
- Creating isolated project workspaces (`/workspaces/<project-id>/`) with `--worktree`
- Implementing atomic task claim (`ZPOPMIN` with Lua) and failure recovery (heartbeat lost → STALE → FAILED/requeue)
- Adding event persistence (`Event` model → DB) and artifact metadata (`checksum`, `version`, `project/task/user` relations)
- Enforcing dangerous-command approval (`approval_policy` smart/manual; never `--yolo` by default)
- Running Phase 4 audit: verify real execution, real Docker services, real authorization (user A/B/C), real workspace isolation, real cancellation/timeout, real clean-environment migration
- Creating `docs/PHASE4_AUDIT.md` and `docs/PHASE4_E2E_RESULT.md` with executable evidence (real IDs, timestamps, outputs)

## Hard Invariants (from Phase 0-4 architecture)

- **Agent Role ≠ Worker**: Role = logical profile (`AgentRole` enum); Worker = reusable resource (`WorkerPool`). Never create a permanent Hermes instance per role. Always load role dynamically (`adapter.create_session()` → `assign_role()` → `ExecutionContext.role`).
- **Security before execution**: Auth (`auth.py`) + authorization (`authorization.py`) must work before any agent execution. RBAC (`Admin`/`User`) + ownership (`owner_id` on Project, `author_id` on Artifact) enforced at handler level, not UUID obscurity.
- **Workspace isolation**: Every project workspace (`/workspaces/<project-id>/`) must pass `Path.resolve().relative_to(allowed_base)` check. Never expose arbitrary filesystem paths through API.
- **Secrets never in prompts/events/logs/API**: `ExecutionContext` excludes secrets; adapter prompt excludes secrets; `user_api_keys` stored encrypted (Fernet); `structlog` redactors enabled. Never pass `JWT_SECRET`, `ENCRYPTION_KEY`, DB/Redis credentials, AI provider keys, Telegram tokens through `-z`, `ExecutionContext`, `events` metadata, `artifact` metadata, or `worker_logs`.
- **No `--yolo` by default**: Dangerous commands (`rm -rf`, `sudo`, `systemctl`, `iptables`, destructive DB ops) must enter approval mechanism. Adapter uses `approval_policy: "smart"` (not `"off"`). Never silently bypass Hermes approval.
- **Provider-agnostic adapter**: `AgentRuntimeInterface` abstracts runtime; `HermesRuntimeAdapter` is one adapter. Future adapters (`OpenAIRuntimeAdapter`, `AnthropicRuntimeAdapter`, `LocalRuntimeAdapter`) plug in without redesigning orchestration. Adapter is injectable (`get_adapter()` returns `AgentRuntimeInterface`).
- **MAX_CONCURRENT_WORKERS=2**: Default via `.env` / `get_settings()`. Configurable through environment (`max_concurrent_workers`). Not optimized for high counts yet. Worker pool (`WorkerPool`) respects this limit.
- **Audit truth**: Phase 4 audit (`docs/PHASE4_AUDIT.md`) must classify each component: `IMPLEMENTED`, `PARTIAL`, `NOT IMPLEMENTED`, `SIMULATED`, `DOCUMENTED`. Never convert `PARTIAL`/`NOT VERIFIED` into `PASS`. Never describe simulated tests as integration verification. Never describe planned flows as executed E2E.

## References

- `references/cli-reference.md` (Hermes CLI invocation: `-z`, `-t`, `--worktree`, `--resume`, `--skills`, `--yolo`)
- `references/configuration.md` (Hermes config sections: agent, approvals, memory, security, delegation, terminal)
- `references/security-privacy.md` (Secret redaction, PII, approval modes)
- `docs/HERMES_INTEGRATION.md` (Hermes discovery: CLI-based, not Python library; adapter uses `subprocess.run`) — Phase 4 file
- `docs/AGENT_ARCHITECTURE.md` (`AgentRole` enum, `AgentRuntimeInterface`, `HermesRuntimeAdapter` definition)
- `docs/WORKER_ARCHITECTURE.md` (Worker lifecycle: OFFLINE → IDLE → ASSIGNED → EXECUTING → COMPLETING → IDLE; isolation)
- `docs/SECURITY_ARCHITECTURE.md` (Auth/authz, RBAC, secret handling, tool permissions, approval center, documented limitations)
- `backend/app/core/runtime/agent_runtime.py` — adapter source (Phase 4 file; fixed broken references: `AgentRole.GENERALIST` → `CHIEF_ORCHESTRATOR`, `Status.RUNNING` added, `stream_events` return type fixed, `schedule_task` variable fixed)
- `backend/app/services/worker.py` — worker service (Phase 4 file; fixed broken references: `WorkerStatus.RUNNING`/`WAITING` checked, `structlog.get_logger()` imported, `Task` model import, `datetime`/`timezone` used correctly, duplicate `start_worker_pool` removed, `schedule_task` `context` variable fixed)
- `backend/worker.py` — executable worker entrypoint (Phase 4 file; independent execution; connects DB/Redis; claims tasks; uses adapter; handles cancellation; heartbeat)
- `docs/PHASE4_AUDIT.md` — audit table (IMPLEMENTED / PARTIAL / NOT IMPLEMENTED / SIMULATED / DOCUMENTED) — Phase 4 file
- `docs/PHASE4_E2E_RESULT.md` — E2E evidence template (timestamp, commit, Docker services, real IDs, actual outputs) — Phase 4 file

## Supporting Files

- `references/hermes_cli.md` — Hermes CLI flags summary (`-z`, `-t`, `--worktree`, `--resume`, `--skills`, `--profile`, `--yolo`, `--safe-mode`, `--worktree` isolation)
- `references/workspace_isolation.md` — Isolation mechanism (`Path`, `relative_to`, allowed base `/workspaces/`, no chroot/container isolation claim unless verified by `docker inspect`)
- `references/approval_security.md` — Approval mechanism boundary (Hermes owns mechanism; adapter configures via `approval_policy`; dangerous actions must block; manual approval must allow continuation; denial must prevent continuation; never describe `--yolo` as secure)
- `templates/agent_execution_context.yaml` — `ExecutionContext` starter (project, task, role, allowed_tools, approval_policy, workspace_path, max_execution_time, max_output_size; excludes secrets)
- `templates/phase4_audit_table.md` — Audit table template (Component, Claimed, Actual, Status, Evidence; STATUS options: PASS, FAIL, PARTIAL, NOT VERIFIED, SIMULATED)
- `scripts/verify_phase4_e2e.py` — Reproducible E2E script (register, login, create project/task, claim/execution via adapter, artifact retrieval, clean environment, real IDs only, timestamp, commit hash)
