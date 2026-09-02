# RESEARCH.md

## Hermes Agent Architecture Analysis

### Key Findings

- **Hermes Agent** is an open-source AI agent framework by Nous Research
- Runs on Linux, macOS, Windows, WSL
- Works with 20+ LLM providers (OpenRouter, Anthropic, OpenAI, Google, DeepSeek, xAI, local models)
- Multi-platform gateway: Telegram, Discord, Slack, WhatsApp, iMessage, Signal, Email, SMS, Matrix, Teams, etc.
- Multiple surfaces: CLI, Ink TUI, native Electron desktop app, Web dashboard, ACP server for IDEs

### Integration Points (from Skill docs)

| Component | Integration Method |
|-----------|-------------------|
| **Agent Execution** | `terminal()` tool with `hermes chat` command; or spawning `hermes` subprocess |
| **Tool System** | Hermes toolsets: `web`, `terminal`, `browser`, `file`, `code_execution`, `coding`, `computer_use`, etc. |
| **Skills** | Load via `--skills` flag or `hermes skills install`; saved to `~/.hermes/skills/` |
| **Memory** | Persistent cross-session memory; SQLite-backed `~/.hermes/state.db`; FTS5 search |
| **Subagents** | `delegate_task` spawns isolated agents; `terminal(background=true)` for long missions |
| **Messaging Integrations** | Gateway plugin system; 20+ messaging platform adapters |
| **MCP Servers** | Native MCP support; `hermes mcp add/remove/list/test/install` |
| **Cron/Background** | `cronjob` tool for scheduled tasks; `hermes cron create` |
| **Profiles** | Isolated configs, sessions, skills, memory via `~/.hermes/profiles/<name>/` |
| **Plugins** | Desktop UI plugins, TUI widgets, skins, pet mascots |
| **Project Context** | `AGENTS.md`, `SOUL.md`, `memory/` files in project root |

### Design Principles for NexusForge Hermes Integration

1. **Never tightly couple core to Hermes internals** — implement Agent Runtime Abstraction Layer
2. **Agent Roles = logical profiles**, not permanent Hermes processes
3. **Workers = reusable execution resources** dynamically load roles
4. **Profile-safe paths**: use `get_hermes_home()` or `$HERMES_HOME`, never hardcode `~/.hermes`
5. **Configuration in `config.yaml`**, secrets in `.env` under `$HERMES_HOME`
6. **Use `hermes config set` never hand-edit config.yaml** — stray indents break live gateway
7. **Profile isolation**: each profile has its own skills/, plugins/, cron/, memories/

### Reusable Components to Preserve

- Agent execution model
- Tool system with permission levels (SAFE/LIMITED/PRIVILEGED/DANGEROUS)
- Memory architecture (system/user/project/task scopes)
- Skill management and loading
- Profile isolation pattern
- CLI routing and flag system
- Gateway platform adapters

## Hermes WebUI Architecture Analysis

### Surface Capabilities

- Web admin panel + embedded chat (`hermes dashboard`)
- Messaging channels catalog (MCP servers)
- Webhook routes and event-driven runs
- Profile builder
- MCP catalog management

### UI Concepts for NexusForge

- **Dashboard**: Modern AI Mission Control
- **AI Mission Control interface**: Dark-first, premium, futuristic, clean, responsive
- **Animation**: Communicate activity without sacrificing usability
- **Agent visualization**: Logical roles vs physical workers represented differently
- **Real-time updates**: WebSocket-based activity feeds

### Important Theming Rules (from Hermes skill)

- **Skins apply themselves**: `hermes config set display.skin <name>` — every surface repaints live within ~1s
- **To tweak one color**: edit the ACTIVE skin — never fork `default`, which drops the palette and resets background
- NexusForge should have its own identity — can reuse useful components where compatible

### API Endpoints (from webui/dashboard patterns)

- `/api/chat/send` — send chat message
- `/api/sessions` — list sessions
- `/api/history` — conversation history
- WebSocket endpoint for real-time updates

## Technology Decisions

- **Frontend**: React + TypeScript (compatible with Hermes WebUI concepts)
- **Backend**: Python + FastAPI (modern, async, good OpenAPI support)
- **Database**: PostgreSQL (primary) + Redis (task queue)
- **Task Queue**: Redis-backed (reliable open-source queue)
- **Runtime**: Hermes Agent as first runtime adapter via abstraction layer
- **Deployment**: Docker + Docker Compose (single-server initial, multi-server future)
- **WebSockets**: For real-time activity and task tracking
- **Authentication**: JWT-based with optional email verification
- **Authorization**: RBAC with Admin/User initial roles, extensible
- **Real-time**: Server-Sent Events or WebSocket

## Research Artifacts

- Interviewed Hermes Agent docs structure and CLI reference
- Analyzed Hermes WebUI patterns and dashboard architecture
- Identified Hermes Agent runtime integration points
- Documented Hermes Agent memory and profile isolation
- Extracted Hermes agent execution model and tool permission system