# NexusForge Handover Document

## System Architecture

NexusForge is a full-stack application composed of the following services:

| Service | Technology | Port | Purpose |
|---------|------------|------|---------|
| **Backend API** | FastAPI (Python) | 8000 | REST API, JWT authentication, WebSocket support |
| **Frontend** | React + Vite (TypeScript) | 3000 | Single-page application |
| **PostgreSQL** | PostgreSQL 15 | 5432 | Primary database |
| **Redis** | Redis 7 | 6379 | Caching, task queues, Celery broker |
| **Celery Worker** | Python | — | Background task processing |
| **Nginx** | Nginx | 80/443 | Reverse proxy (routes `/api/` and `/ws/` to backend) |

### Network Topology

```
┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│   Nginx     │ (port 80/443)
└─────────────┘     └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌────────┐   ┌──────────┐ ┌──────────┐
         │/api/*  │   │ /ws/*    │ │ /*       │
         ▼        ▼   ▼          ▼ ▼          ▼
      ┌─────────────────────────────────────────┐
      │           Backend (FastAPI)             │
      │  • REST API (/api/*)                    │
      │  • WebSocket (/ws/*)                    │
      │  • JWT Auth                             │
      └─────────────────────────────────────────┘
              │            │            │
              ▼            ▼            ▼
         ┌────────┐   ┌──────────┐ ┌──────────┐
         │Postgres│   │  Redis   │ │  Celery  │
         └────────┘   └──────────┘ └──────────┘
```

### Nginx Routing Rules

- `/api/` → Stripped, forwarded to `http://backend:8000/` (FastAPI)
- `/ws/` → Stripped, forwarded to `http://backend:8000/` (WebSocket upgrade)
- `/*` → Served by frontend (Vite dev server or static build)

## What Is Currently Working

| Feature | Status | Details |
|---------|--------|---------|
| **JWT Authentication** | ✅ Working | Register: `POST /api/auth/register`, Login: `POST /api/auth/login` |
| **Admin User** | ✅ Seeded | Email: `admin@nexusforge.io` / Password: `password123` |
| **Health Endpoint** | ✅ Working | `GET /api/health` returns 200 |
| **WebSocket Infrastructure** | ✅ Working | `/ws/` routes configured in Nginx and FastAPI |
| **Database Migrations** | ✅ Working | Alembic migrations run on startup |
| **Redis/Celery Queue** | ✅ Connected | Worker processes tasks from Redis queue |

### Verified Credentials
- **Admin**: `admin@nexusforge.io` / `password123`
- **Test User**: `test@nexusforge.io` / `testpass123` (via registration)

### Verified Endpoints
```bash
# Health check
curl http://localhost:3000/api/health
# {"status":"healthy"}

# Register
curl -X POST http://localhost:3000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@test.com","password":"pass123","username":"user"}'

# Login
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@nexusforge.io","password":"password123"}'
# Returns: {"access_token":"...","token_type":"bearer"}
```

## What Remains to Be Fixed

| Area | Issue | Priority |
|------|-------|----------|
| **Mobile Layout** | Responsive breakpoints not fully implemented; cards overflow on small screens | High |
| **Card Styling** | Inconsistent spacing, shadow, and border-radius across card components | Medium |
| **`/projects` Route Data Mapping** | Frontend expects different shape than backend returns; needs transformation layer | High |
| **WebSocket Message Types** | Typing indicators and presence events not yet wired | Low |
| **E2E Tests** | Playwright tests not configured | Medium |

## Local Setup Guide

### Prerequisites
- Docker Desktop (recommended) or Docker Engine + Docker Compose v2
- Node.js 20+ (for frontend development outside Docker)
- Python 3.12+ (for backend development outside Docker)

---

### Option 1: Docker Desktop (Recommended)

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd NexusForge

# 2. Copy environment template
cp .env.example .env

# 3. Edit .env if needed (defaults work for local dev)
# Optional: set JWT_SECRET_KEY to a secure random string

# 4. Start all services
docker compose up -d --build

# 5. Verify services are healthy
docker compose ps

# 6. Access the application
# Frontend: http://localhost:3000
# API: http://localhost:3000/api
# Health: http://localhost:3000/api/health

# 7. View logs
docker compose logs -f backend
docker compose logs -f frontend
```

#### Docker Service URLs (Local)
| Service | URL |
|---------|-----|
| Frontend (Nginx) | http://localhost:3000 |
| Backend API | http://localhost:3000/api |
| Health Check | http://localhost:3000/api/health |
| WebSocket | ws://localhost:3000/ws |

---

### Option 2: Local Development (npm + uvicorn)

#### Backend (FastAPI)
```bash
cd /home/yellowdeerco/NexusForge

# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Set environment variables
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/nexusforge
export REDIS_URL=redis://localhost:6379/0
export JWT_SECRET_KEY=dev_secret_key
export SECRET_KEY=dev_secret_key
export ENCRYPTION_KEY=dev-encryption-key-32-bytes-base64-c3RhY2xl
export MAX_CONCURRENT_WORKERS=2
export CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# 4. Start PostgreSQL and Redis (via Docker or local install)
docker run -d --name postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=nexusforge -p 5432:5432 postgres:15-alpine
docker run -d --name redis -p 6379:6379 redis:7-alpine

# 5. Run migrations
cd backend
alembic -c app/alembic.ini upgrade head

# 6. Start backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 7. Start Celery worker (separate terminal)
celery -A app.worker worker --loglevel=info --concurrency=2
```

#### Frontend (Vite + React)
```bash
cd /home/yellowdeerco/NexusForge/frontend

# 1. Install dependencies
npm install

# 2. Create .env.local (optional, for custom API URL)
echo "VITE_API_URL=http://localhost:8000" > .env.local

# 3. Start dev server
npm run dev

# Frontend available at http://localhost:3000 (proxies /api to backend)
```

---

### Useful Commands

| Task | Command |
|------|---------|
| Rebuild and restart | `docker compose up -d --build` |
| View logs | `docker compose logs -f [service]` |
| Run migrations manually | `docker compose exec backend alembic -c /app/app/alembic.ini upgrade head` |
| Open backend shell | `docker compose exec backend bash` |
| Open postgres shell | `docker compose exec postgres psql -U postgres -d nexusforge` |
| Stop all services | `docker compose down` |
| Stop + remove volumes | `docker compose down -v` |
| Run tests | `docker compose exec backend pytest` |

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `REDIS_URL` | Yes | — | Redis connection string |
| `JWT_SECRET_KEY` | Yes | — | Secret for JWT signing (min 32 chars) |
| `SECRET_KEY` | Yes | — | General secret key |
| `ENCRYPTION_KEY` | Yes | — | 32-byte base64 key for encryption |
| `MAX_CONCURRENT_WORKERS` | No | 2 | Worker pool size |
| `CORS_ORIGINS` | No | `http://localhost:3000,http://localhost:8000` | Allowed CORS origins |

See `.env.example` for complete list.

---

## Project Structure

```
NexusForge/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routes
│   │   ├── models/        # SQLAlchemy models
│   │   ├── db/            # Database session
│   │   ├── auth.py        # JWT authentication
│   │   ├── worker.py      # Celery worker
│   │   └── main.py        # FastAPI application
│   ├── alembic/           # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/         # React pages
│   │   ├── components/    # Reusable components
│   │   ├── services/      # API clients
│   │   └── hooks/         # Custom React hooks
│   ├── Dockerfile.frontend
│   ├── package.json
│   └── vite.config.ts
├── nginx.conf             # Reverse proxy config
├── docker-compose.yml     # Service orchestration
├── .env.example           # Environment template
└── HANDOVER.md            # This file
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `404 Not Found` on `/api/auth/*` | Ensure Nginx `proxy_pass` has trailing slash: `proxy_pass http://backend:8000/;` |
| Database connection failed | Wait for postgres healthcheck; check `docker compose logs postgres` |
| Worker not processing tasks | Check `docker compose logs worker`; verify Redis connection |
| Frontend blank page | Check `docker compose logs frontend`; verify Vite build output |
| JWT verification failed | Ensure `JWT_SECRET_KEY` matches between backend and any external services |

---

## Quick Verification Checklist

After setup, verify:
- [ ] `curl http://localhost:3000/api/health` returns `{"status":"healthy"}`
- [ ] Login with `admin@nexusforge.io` / `password123` works
- [ ] Register a new user via frontend
- [ ] WebSocket connection establishes (check browser devtools Network tab)
- [ ] Celery worker shows as active in logs
- [ ] PostgreSQL has `users` table with admin user

---

## Contact & Support

For questions about this handover, refer to:
- Architecture docs: `docs/SYSTEM_ARCHITECTURE.md`
- API docs: `docs/AUTHENTICATION.md`
- Phase audits: `docs/PHASE*.md`

---

*Document generated: 2026-09-12*
*Version: 1.0*
*Repository: NexusForge*