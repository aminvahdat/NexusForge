# PRODUCT_ARCHITECTURE.md

## Product Vision

NexusForge is a self-hosted, multi-agent orchestration platform that lets users submit a high-level task in natural language and automatically understands, analyzes, plans, decomposes, executes, and delivers structured results.

**Core Promise**: Submit "Build a SaaS application for invoice generation" — NexusForge coordinates planning, research, architecture, implementation, testing, security review, and deployment preparation through dynamic logical agent roles and a configurable pool of reusable AI-powered workers.

## Target Users

- **Developers** who want to build full-stack applications with minimal manual coordination
- **Teams** that need consistent software delivery with automated quality gates
- **Research-oriented organizations** requiring evidence-based technology decisions
- **Self-hosters** who prefer local, private AI-powered orchestration
- **Smart-home/IoT companies** (like Yellowdeer Co.) needing custom automation platforms

## Core User Journeys

### Journey 1: Submit a Project

```
User types request → NexusForge analyzes → Asks clarification questions (if needed)
→ Creates structured project plan → Decomposes into tasks → Assigns logical roles
→ Executes in parallel → Reviews outputs → Delivers final result
```

### Journey 2: Monitor Progress

```
Login → Dashboard shows active projects/running workers/tasks
→ Click project → Workspace view with milestones/task graph/agent activity
→ Real-time activity feed shows task status changes
→ Approve/reject dangerous operations via Approval Center
→ Receive Telegram notifications for key milestones
```

### Journey 3: Manage Projects

```
View all projects → Select project → See status/progress/active roles/workers
→ Browse artifacts (requirements, architecture, API specs, test reports)
→ Review security reports → Download deployment files
→ Retry failed tasks → Cancel stalled projects
```

## Feature Specification

### P0 — Core Orchestration (Phase 1-3)

| Feature | Description |
|---------|-------------|
| Project Creation | Submit high-level request; auto-generate structured project |
| Task System | Tasks with dependencies, priority, status, acceptance criteria |
| Dependency Graph | Tasks form a DAG; independent tasks execute in parallel |
| Task Statuses | QUEUED → PLANNING → BLOCKED → READY → RUNNING → WAITING → REVIEWING → NEEDS_REVISION → COMPLETED / FAILED / CANCELLED |
| Chief Orchestrator | Central coordinator; understands intent, selects roles, delegates work |
| Project Planner | Requirements analysis, PRD generation, user stories, milestones |

### P0 — Authentication & Authorization (Phase 3)

| Feature | Description |
|---------|-------------|
| User Registration | Email/password with secure hashing |
| Login/Logout | Session/token-based auth |
| RBAC | Admin/User roles, extensible |
| User Isolation | Users cannot access others' projects, tasks, artifacts, memory, logs |
| Rate Limiting | Protect against brute-force |
| Password Reset | Architecture prepared, optional email verification |

### P1 — Agent Runtime & Workers (Phase 4-8)

| Feature | Description |
|---------|-------------|
| Agent Runtime Interface | Abstraction layer decoupling core from Hermes internals |
| Hermes Runtime Adapter | First implementation of the runtime interface |
| Configurable Worker Pool | `MAX_CONCURRENT_WORKERS` (default: 2); workers are reusable |
| Dynamic Role Loading | Workers load logical agent roles on demand |
| Task Execution | Workers execute tasks with context minimization |

### P2 — Agent Roles & Task Decomposition (Phase 5-7)

| Feature | Description |
|---------|-------------|
| Built-in Agent Roles | Chief Orchestrator, Planner, Architect, Research, UI/UX, Frontend, Backend, Mobile, Database, Security, QA, DevOps |
| Dynamic Temporary Roles | Smart Home Engineer, IoT Engineer, MQTT Specialist, ML Engineer, etc. |
| Task Decomposition | Requirements → Architecture → Implementation → Testing → Deployment |
| Skill Assignment | Workers load required skills per task |
| Human Approval Center | Dangerous commands, production deployment, paid API usage, infrastructure changes |

### P3 — UI & Real-time (Phase 9-10)

| Feature | Description |
|---------|-------------|
| Dashboard | Active projects, running workers/tasks, completed/failed counts, recent activity |
| Projects View | List of user projects with status, progress, active roles/workers |
| Project Workspace | Primary workspace — request, requirements, architecture, milestones, task graph, agent activity, worker activity, artifacts, logs, tests, security reports |
| Agent Cluster Visualization | Animated visualization differentiating logical roles from physical workers |
| Real-time Activity | WebSocket-driven live feed of task and worker events |
| Task Flow Animation | Thinking → Working → Researching → Completed/Failed transitions |

### P4 — Notifications & Polish (Phase 11-13)

| Feature | Description |
|---------|-------------|
| Telegram Notifications | Project started/completed/failed, approval requests, milestones |
| Onboarding Wizard | First-login flow: welcome, profile, AI provider, preferences, Telegram setup |
| Tests | Unit, integration, critical e2e (auth, authz, isolation, dependencies, scheduling, concurrency, retry, approval) |
| Security Review | Full internal review before first release |
| Documentation | README, installation guide, architecture docs, CONTRIBUTING, SECURITY |

## Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| **Self-hosted** | Docker Compose on Ubuntu Server |
| **Scalable** | Single-server initial, multi-server future |
| **Secure** | Secure by default; RBAC; secrets never in logs or frontend |
| **Modular** | Clean architecture; plugin/extensible; provider-agnostic |
| **Observable** | Structured logging; health checks; future monitoring integration |
| **Accessible** | Dark-first; responsive; respects reduced-motion preferences |
| **Testable** | Every feature has tests; no untested features claimed complete |

## Key Design Decisions

1. **Agent Roles ≠ Workers**: Logical profiles vs execution resources
2. **Modular Monolith**: First version prefers modular monolith with worker processes
3. **Provider-Agnostic**: Core orchestration independent of Hermes internals
4. **Runtime Abstraction**: Agent Runtime Interface with Hermes Runtime Adapter first
5. **Minimum Viable Workers**: Default 2; configurable up to 10+
6. **Context Minimization**: Workers receive only relevant project context
7. **Artifact Communication**: Agents communicate through structured artifacts
8. **Security First**: Authentication and authorization built before agent system

## Platform Constraints

- **Primary**: Ubuntu Server with Docker + Docker Compose
- **No Kubernetes** (future enhancement)
- **No managed cloud** dependency
- **No proprietary database** (PostgreSQL + Redis)
- **No proprietary queue** (Redis-backed queue)
- **No specific hosting provider** dependency