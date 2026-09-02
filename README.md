# NexusForge

A self-hosted, multi-agent orchestration platform for autonomous software development and complex technical tasks.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue)](https://docs.docker.com/get-docker/)
[![Ubuntu 22.04+](https://img.shields.io/badge/Ubuntu-22.04+-orange.svg)](https://ubuntu.com/download/server)

## Overview

NexusForge is a real self-hosted AI orchestration platform — not a chatbot with multiple personalities. It allows users to submit high-level tasks in natural language and automatically coordinates planning, research, architecture, implementation, testing, security review, and deployment preparation through dynamic logical agent roles and a configurable pool of reusable AI-powered workers.

### Key Features

- **Natural Language Task Submission** - Submit tasks like "Build a SaaS application for invoice generation" and get structured results
- **Agent Role System** - 12 built-in logical agent roles (Orchestrator, Planner, Architect, Security, QA, DevOps, etc.)
- **Dynamic Role Loading** - Workers dynamically load roles; no permanent one-to-one mapping
- **Configurable Worker Pool** - Scale from 1 to 10+ workers based on resources
- **Task Dependency Graphs** - Independent tasks execute in parallel; dependent tasks wait
- **Structured Artifact System** - Requirements, architecture docs, API specs, test reports
- **Multi-Level Memory** - System, user, project, and task-level memory isolation
- **Real-Time Activity** - WebSocket-based live updates of agent and worker status
- **Agent Cluster Visualization** - Animated visualization distinguishing logical roles from physical workers
- **Security First** - Authentication before agent system; RBAC; user isolation; approval center
- **Telegram Notifications** - Project milestones, approvals, completions, failures

### Architecture Highlights

```
Agent Roles ≠ Workers
Workers are execution resources that dynamically load logical roles
```

- **Agent Runtime Interface** - Provider-agnostic abstraction with Hermes Agent as first adapter
- **Modular Monolith** - Clean architecture with worker processes (not microservices)
- **Self-Hosted** - Runs on a single Ubuntu server with Docker Compose
- **Scalable Design** - Horizontal scaling via configurable worker count; multi-server future

### Technology Stack

| Component | Technology |
|-----------|-----------|
| Frontend | React + TypeScript |
| Backend | Python + FastAPI |
| Database | PostgreSQL |
| Queue | Redis |
| Agent Runtime | Hermes Agent (via abstraction layer) |
| Deployment | Docker + Docker Compose |
| Real-time | WebSockets |

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd nexusforge

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Start the system
docker compose up -d
```

Open `http://localhost:3000` in your browser.

### First-Time Setup

1. **Create an account** - Register with email and secure password
2. **Complete onboarding wizard** - Configure profile, AI provider, preferences
3. **Create your first project** - Submit a high-level task description
4. **Monitor progress** - Watch tasks execute in real-time
5. **Review artifacts** - Access requirements, architecture, code, tests
6. **Approve dangerous operations** - Review and approve deployment actions

## System Requirements

### Minimum Requirements
- **OS**: Ubuntu 22.04 LTS or newer
- **CPU**: 2 cores (4 cores recommended)
- **Memory**: 4GB RAM (8GB recommended for 2+ workers)
- **Storage**: 20GB free space
- **Docker**: Docker Engine 24.0+
- **Docker Compose**: 2.20+

### Recommended Requirements
- **OS**: Ubuntu 22.04 LTS
- **CPU**: 4+ cores
- **Memory**: 8GB+ RAM
- **Storage**: 50GB+ SSD
- **Network**: Broadband internet connection for AI provider access

### Prerequisites

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin
```

Restart your session or log out and back in for docker group membership to take effect.

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/nexusforge/nexusforge.git
cd nexusforge
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Required settings
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/nexusforge
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=your-secret-key-change-this-in-production

# AI Provider Keys (required for agent execution)
OPENAI_API_KEY=your-api-key  # or ANTHROPIC_API_KEY, etc.

# Optional: Configure worker count
MAX_CONCURRENT_WORKERS=2  # Adjust based on server resources
```

### 3. Start Services

```bash
# Development mode
npm run dev  # Starts frontend
python -m uvicorn backend.app.main:app --reload  # Starts backend

# Production mode (Docker)
docker compose up -d
```

Access the web interface at `http://localhost:3000`.

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# End-to-end tests (requires running services)
cd tests/e2e
npm test
```

### Building for Production

```bash
# Build Docker images
docker compose build

# Deploy with production settings
docker compose -f docker-compose.prod.yml up -d
```

## Architecture

NexusForge follows a clean modular architecture with the following components:

### System Components

1. **Web Frontend** - React + TypeScript with modern UI design
2. **API Gateway** - FastAPI with authentication and authorization
3. **Chief Orchestrator** - Central coordinator for task management
4. **Task Planner** - Requirements analysis and task decomposition
5. **Task Queue** - Redis-backed queue for task scheduling
6. **Worker Pool** - Configurable pool of Hermes-powered workers
7. **Agent Roles** - Dynamic logical expertise profiles
8. **Artifact Store** - Structured artifact storage and management
9. **Project Memory** - Project-specific knowledge management
10. **Notification Service** - Telegram and email notifications

### Key Design Principles

- **Agent Roles ≠ Workers**: Logical profiles vs execution resources
- **Dynamic Role Loading**: Workers load roles at task time
- **Context Minimization**: Workers receive only relevant context
- **Security Boundaries**: Process-level isolation and least privilege
- **Provider Agnostic**: Runtime abstraction allows multiple AI providers

For detailed architecture documentation, see [docs/](docs/).

## Agent Roles

NexusForge includes 12 built-in logical agent roles:

| Role | Responsibilities |
|------|-----------------|
| Chief Orchestrator | Understands intent, selects roles, manages execution |
| Project Planner | Requirements analysis, PRD generation, milestones |
| Software Architect | Technology selection, system architecture |
| Research Agent | Evidence-based recommendations, documentation validation |
| UI/UX Agent | User flows, responsive design, design systems |
| Frontend Agent | Component implementation, state management |
| Backend Agent | API development, business logic |
| Mobile Agent | iOS/Android/cross-platform development |
| Database Agent | Schema design, migrations, performance |
| Security Agent | Authentication, authorization, vulnerability review |
| QA Agent | Unit, integration, end-to-end testing |
| DevOps Agent | Docker, CI/CD, deployment, monitoring |

Additionally, temporary roles can be created for domain-specific tasks (Smart Home Engineer, IoT Engineer, etc.).

For more details, see [docs/AGENT_ARCHITECTURE.md](docs/AGENT_ARCHITECTURE.md).

## Security

NexusForge is designed with security as a first principle:

- **Authentication First**: Authentication implemented before agent system
- **User Isolation**: Users never access others' projects, tasks, artifacts, memory
- **Role-Based Access Control**: Admin and User roles with extensible architecture
- **Secret Management**: Secrets never in logs, never exposed to frontend
- **Worker Isolation**: Process-level isolation with permission boundaries
- **Approval Center**: Dangerous operations require explicit user approval

See [docs/SECURITY_ARCHITECTURE.md](docs/SECURITY_ARCHITECTURE.md) for the full security architecture.

Also see [SECURITY.md](SECURITY.md) for security policies and vulnerability reporting.

## Real-Time Features

The web interface provides real-time updates through WebSockets:

- **Dashboard**: Active projects, running workers, task status
- **Agent Visualization**: Animated role-to-worker mapping
- **Task Flow**: Live status changes (Thinking → Working → Completed)
- **Activity Feed**: Real-time task events and updates

## Notifications

### Telegram Notifications
Configure Telegram notifications in the onboarding wizard:

1. Create a Telegram bot via [@BotFather](https://t.me/botfather)
2. Get the bot token
3. Configure in `.env` or settings page
4. Select notification preferences

Supported notifications:
- Project started
- Milestone completed
- Approval required
- Project completed
- Project failed

Notification messages include project details, role information, and milestone status. They never contain secrets.

## Documentation

- [RESEARCH.md](docs/RESEARCH.md) - Hermes Agent architecture analysis
- [PRODUCT_ARCHITECTURE.md](docs/PRODUCT_ARCHITECTURE.md) - Product vision and feature specification
- [SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md) - System architecture and tech stack
- [AGENT_ARCHITECTURE.md](docs/AGENT_ARCHITECTURE.md) - Agent role system and runtime abstraction
- [WORKER_ARCHITECTURE.md](docs/WORKER_ARCHITECTURE.md) - Worker pool and execution model
- [SECURITY_ARCHITECTURE.md](docs/SECURITY_ARCHITECTURE.md) - Security model and authorization
- [IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) - Phased implementation plan

## Project Structure

```
nexusforge/
├── docs/                      # Architecture documentation
├── frontend/                  # React + TypeScript frontend
│   └── src/
│       ├── components/        # UI components
│       ├── pages/             # Page components
│       ├── services/          # API client
│       └── store/             # State management
├── backend/
│   └── app/
│       ├── core/              # Core application logic
│       │   ├── orchestration/ # Chief Orchestrator
│       │   ├── agents/        # Agent roles
│       │   ├── workers/       # Worker management
│       │   ├── tasks/         # Task management
│       │   └── memory/        # Memory management
│       ├── api/               # API endpoints
│       ├── services/          # Business logic
│       └── models/            # Data models
├── docker/                    # Docker configuration
├── scripts/                   # Deployment and maintenance scripts
├── tests/                     # Test suite
└── .env.example               # Environment template
```

## Configuration

NexusForge supports extensive configuration through `.env`:

### Core Settings
```
MAX_CONCURRENT_WORKERS=2          # Default: 2 (adjust based on resources)
API_HOST=0.0.0.0                  # API server host
API_PORT=8000                     # API server port
```

### AI Provider Configuration
```
OPENAI_API_KEY=sk-...            # OpenAI API key
ANTHROPIC_API_KEY=sk-ant-...     # Anthropic API key
```

### Security Settings
```
JWT_SECRET_KEY=...                # Secure JWT signing key
DATABASE_URL=postgresql://...    # Database connection
REDIS_URL=redis://...            # Redis connection
```

For the complete list of configuration options, see `.env.example`.

## Deployment

### Single Server (Recommended for First Version)

```bash
docker compose up -d
```

### Multi-Server (Future)

The architecture supports future multi-server deployment:
- Separate worker nodes
- Central database and queue
- Distributed worker coordination

## Testing

NexusForge includes comprehensive testing:

- **Unit Tests**: Component-level testing
- **Integration Tests**: Service interaction testing
- **End-to-End Tests**: Full workflow testing

Critical test coverage:
- Authentication and authorization
- User isolation
- Task dependencies
- Worker scheduling
- Worker concurrency limits
- Task retry logic
- Approval system

## Contributing

We welcome contributions! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before submitting pull requests.

### Development Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes with tests
# Submit pull request
```

### Code Quality
- All code must include appropriate tests
- Documentation must be updated for new features
- Security implications must be reviewed
- Breaking changes require migration notes

## Roadmap

### Phase 1: Foundation ✅
- Project structure and configuration
- Database and Docker setup
- Basic API framework

### Phase 2: Authentication ⚡
- User registration and login
- JWT authentication
- RBAC implementation

### Phase 3: Projects ⚡
- Project creation and management
- Workspace functionality
- Artifact system

### Phase 4: Agent Runtime ⚡
- Runtime abstraction layer
- Hermes adapter
- Basic worker execution

### Phase 5: Task System ⚡
- Task creation and dependencies
- Task scheduling
- Execution tracking

### Phase 6: UI and Real-Time ⚡
- Dashboard and workspace
- Real-time updates
- Agent visualization

### Phase 7: Notifications and Polish ⚡
- Telegram notifications
- First login onboarding wizard
- Final testing and release

## Support

For questions and support:
- **GitHub Issues**: Technical issues and feature requests
- **Documentation**: Detailed architecture documentation in [docs/](docs/)
- **Community**: Discussions in repository issues

## License

NexusForge is licensed under the MIT License. See [LICENSE](LICENSE) for details.

This is an open-source project designed for publication on GitHub. The repository is designed to work for any user after cloning and configuring their own environment, with neutral naming throughout the codebase and no company-specific assumptions.

---

Built with the understanding that Agent Roles are logical profiles, not permanent processes, and Workers are reusable execution resources that dynamically load roles. The architecture supports both single-server deployment and future multi-server scaling without redesigning the entire system.
