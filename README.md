# NexusForge — Autonomous Software Development Platform

## Overview
NexusForge is a self-hosted, multi-agent orchestration platform for autonomous software development. It provides a premium, modern UI for managing projects and tasks with real backend integration.

## Architecture

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 15 with asyncpg
- **Cache/Queue**: Redis 7-alpine
- **Migrations**: Alembic (12 tables)
- **Architecture**: Agent Runtime Interface + HermesAdapter

### Frontend
- **Framework**: React 18 + TypeScript 5
- **Build Tool**: Vite
- **Styling**: Custom CSS with design system tokens
- **Routing**: React Router v6
- **HTTP Client**: Axios (centralized API client)
- **UI/UX**: AI-Native design system (ui-ux-pro-max)

### Infrastructure
- **Containerization**: Docker Compose
- **Services**: postgres:15-alpine, redis:7-alpine, backend, worker, migrations, frontend
- **Network**: nexusforge-network (bridge)
- **Volumes**: postgres_data, redis_data

## Quick Start

### Prerequisites
- Ubuntu 20.04 LTS or later
- Docker v20.10+
- Docker Compose v2 (or v1)
- Git

### Setup
```bash
# Clone the repository
git clone https://github.com/yellowdeerco/nexusforge.git
cd nexusforge

# Copy environment template
cp .env.example .env
# Edit .env to set your secrets

# Start all services
docker compose up -d

# Check service status
docker compose ps

# View backend logs
docker compose logs backend

# Run migrations (automatic via docker-compose)
docker compose exec migrations alembic -c /app/app/alembic.ini upgrade head
```

### Access the Application
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (when debug mode)
- **Frontend**: http://localhost:3000
- **Worker Dashboard**: http://localhost:8000/workers

### Verify Setup
```bash
# Check all services are running
docker compose ps

# Test backend health
curl http://localhost:8000/api/health

# Test database connection
docker compose exec postgres psql -U nexusforge -d nexusforge -c "SELECT 1;"

# Test Redis connection
docker compose exec redis redis-cli ping
```

## Project Structure

```
nexusforge/
├── backend/             # FastAPI backend application
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # Business logic services
│   │   ├── config/      # Application configuration
│   │   └── core/        # Core application logic
│   ├── alembic/         # Database migrations
│   ├── alembic.ini      # Alembic configuration
│   ├── Dockerfile       # Docker image for backend/worker/migrations
│   └── worker.py        # Worker process
├── frontend/            # React frontend application
│   ├── src/
│   │   ├── pages/       # Page-level components
│   │   ├── components/  # Reusable components
│   │   ├── services/    # API client modules
│   │   ├── types/       # TypeScript type definitions
│   │   └── App.tsx      # Main application
│   ├── package.json     # Node.js dependencies
│   └── vite.config.ts   # Vite configuration
├── docker-compose.yml   # Multi-service Docker orchestration
├── .env.example         # Environment variables template
├── Dockerfile           # Docker image definition
├── LICENSE              # MIT License
├── README.md            # This file
├── docs/                # Documentation
│   ├── DEPLOYMENT.md    # Deployment guide
│   ├── DATABASE.md      # Database schema documentation
│   └── PHASE53_AUDIT.md # Phase 5.3 audit
└── design-system/       # UI/UX design system
    └── nexusforge/
        └── MASTER.md    # Design system master document
```

## API Endpoints

### Health & Readiness
- `GET /api/health` - Health check endpoint
- `GET /api/health/readiness` - Readiness check with DB/Redis status
- `GET /` - Root endpoint

### Projects
- `GET /api/projects` - List all projects
- `GET /api/projects/:id` - Get project by ID
- `POST /api/projects` - Create a new project

### Tasks
- `GET /api/projects/:id/tasks` - List tasks for a project
- `GET /api/tasks/:id` - Get task by ID
- `POST /api/projects/:id/tasks` - Create a task
- `PUT /api/tasks/:id` - Update a task
- `PUT /api/tasks/:id/status` - Update task status

### Workers
- `GET /api/workers/status` - Get worker pool status

### Authentication (Phase 3+)
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/auth/me` - Get current user

## Configuration

### Environment Variables
All configuration is environment-driven. See `.env.example` for all available options.

Key environment variables:
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` - Database configuration
- `DATABASE_URL` - Full database connection URL
- `REDIS_URL` - Redis connection URL
- `SECRET_KEY`, `JWT_SECRET_KEY` - Security keys
- `MAX_CONCURRENT_WORKERS` - Worker pool size (default: 2)
- `AI_PROVIDER`, `AI_MODEL` - Default AI provider/model
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` - AI provider API keys

### AI Provider Configuration
NexusForge is provider-agnostic. Configure your preferred AI provider via environment variables:
- `OPENAI_API_KEY` - OpenAI GPT models
- `ANTHROPIC_API_KEY` - Anthropic Claude models
- `AI_PROVIDER`, `AI_MODEL` - Provider and model selection

## Development

### Backend Development
```bash
# Run backend with hot reload
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Development
```bash
# Run frontend with hot reload
cd frontend
npm run dev
```

### Running Tests
```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd frontend
npm run test
```

## Design System

The UI follows the NexusForge design system defined in `design-system/nexusforge/MASTER.md`.

Key design principles:
- **AI-Native UI**: Chatbot, conversational, streaming text aesthetics
- **Purple/Cyan palette**: Professional AI/tech brand identity
- **Inter font**: Modern, developer-friendly typography
- **Premium quality**: Minimal, sophisticated, luxurious feel
- **Accessible**: WCAG AA compliant, keyboard navigable

## Security

- All API endpoints are protected with environment-driven secrets
- JWT authentication implemented in Phase 3
- RBAC (Role-Based Access Control) available
- Agent tool permissions (SAFE/LIMITED/PRIVILEGED/DANGEROUS)
- Approval center for dangerous operations
- No secrets in logs (structured logging with redaction)

## Contributing

See `CONTRIBUTING.md` for contribution guidelines.

## License

This project is licensed under the MIT License - see `LICENSE` for details.

## Status

Phase 5.3 complete — Real Project & Task Management UI implemented.
Phase 5.4 pending — Live execution streaming, event timeline, artifact browser.

---

**NexusForge v0.1.0**
Built with ❤️ by the NexusForge team.