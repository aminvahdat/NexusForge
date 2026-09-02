# NexusForge — Multi-Agent Orchestration Platform

A self-hosted platform for autonomous software development with multi-agent orchestration, built on FastAPI, PostgreSQL, Redis, and Hermes Agent.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        NexusForge System                            │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│  │   Frontend   │───▶│    API       │───▶│  PostgreSQL  │         │
│  │  (React/TS)  │    │  (FastAPI)   │    │   (15+)      │         │
│  └──────────────┘    └──────┬───────┘    └──────────────┘         │
│                             │                                       │
│                    ┌────────▼────────┐                              │
│                    │     Redis       │                              │
│                    │    (7+)         │                              │
│                    └─────────────────┘                              │
└─────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- `.env` file with required secrets (see `.env.example`)

### Development Stack

```bash
# 1. Copy environment template and fill in secrets
cp .env.example .env
# Edit .env with your actual values

# 2. Start infrastructure (PostgreSQL, Redis)
docker-compose up -d postgres redis

# 3. Verify services are healthy
docker-compose ps
# Both postgres and redis should show "healthy"

# 4. Run database migrations
docker-compose run --rm backend alembic upgrade head

# 5. Start backend API
docker-compose up -d backend

# 6. Verify API health
curl http://localhost:8000/health
# Expected: {"status": "ok", "checks": {"database": true, "redis": true}}

# 7. Start frontend (optional)
docker-compose up -d frontend
```

### Environment Variables

Required in `.env`:
- `POSTGRES_PASSWORD` — PostgreSQL password
- `REDIS_PASSWORD` — Redis password
- `SECRET_KEY` — Application secret (32+ chars)
- `JWT_SECRET_KEY` — JWT signing key (32+ chars)
- `ENCRYPTION_KEY` — Fernet encryption key for API keys (32 bytes base64)

Optional:
- `MAX_CONCURRENT_WORKERS=2` — Worker pool size
- `AI_PROVIDER=openrouter` — AI provider (future use)
- `ALLOWED_ORIGINS=http://localhost:3000` — CORS whitelist

## Authentication

All API endpoints except `/health`, `/readiness`, `/auth/register`, `/auth/login` require authentication.

### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_email@example.com&password=yourpassword"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Using the Token
```bash
curl -H "Authorization: Bearer <access_token>" http://localhost:8000/api/projects
```

## API Endpoints

### Public
- `GET /` — Root info
- `GET /health` — System health check
- `GET /readiness` — DB + Redis liveness
- `POST /auth/register` — Register user
- `POST /auth/login` — Login and get JWT

### Protected (require `Authorization: Bearer <token>`)
- `GET /auth/me` — Current user
- `POST /api/projects` — Create project
- `GET /api/projects/{id}` — Get project
- `POST /api/projects/{id}/tasks` — Create task
- `GET /api/projects/{id}/tasks` — List tasks
- `GET /api/tasks/{id}` — Get task
- `PUT /api/tasks/{id}` — Update task
- `GET /api/workers/status` — Worker pool status

## Project Structure

```
NexusForge/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes (health, auth, projects, tasks)
│   │   ├── auth/         # JWT authentication
│   │   ├── authorization.py  # RBAC
│   │   ├── config/       # Settings management
│   │   ├── db/           # Database connection
│   │   ├── models/       # SQLAlchemy models
│   │   ├── migrations/   # Alembic migrations
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # DB, Redis services
│   │   └── main.py       # FastAPI app
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/             # React/TypeScript (Phase 4+)
├── docker-compose.yml
├── .env.example
└── docs/
    ├── ARCHITECTURE.md
    ├── AUTHENTICATION.md
    ├── AUTHORIZATION.md
    ├── SECURITY_ARCHITECTURE.md
    └── IMPLEMENTATION_PLAN.md
```

## Security

See `docs/SECURITY_ARCHITECTURE.md` for:
- JWT token strategy
- RBAC design
- Secret handling rules
- API security measures
- Known limitations

## Agent Architecture (Future)

- **Agent Roles** = Logical expertise profiles (Chief, Planner, Architect, etc.)
- **Workers** = Reusable execution resources (configurable pool)
- **Hermes Adapter** = Runtime implementation behind Agent Runtime abstraction

See `docs/AGENT_ARCHITECTURE.md` and `docs/WORKER_ARCHITECTURE.md`.

## License

MIT — see `LICENSE` file.