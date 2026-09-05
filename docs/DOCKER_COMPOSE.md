# NexusForge Docker Configuration

## Services

### Frontend Service
- **Image**: Built from Dockerfile.frontend
- **Port**: 3000
- **Depends**: backend (must be running first)
- **Network**: nexusforge-network
- **Restart**: unless-stopped

### Backend Service
- **Image**: Built from Dockerfile (Python 3.11-slim)
- **Port**: 8000
- **Depends**: postgres (healthy), redis (healthy), migrations
- **Network**: nexusforge-network
- **Volumes**: ./backend/app:/app/app
- **Restart**: unless-stopped

### Worker Service
- **Image**: Built from Dockerfile (Python 3.11-slim)
- **Command**: python worker.py
- **Depends**: postgres, redis, backend
- **Network**: nexusforge-network
- **Volumes**: ./backend/app:/app/app
- **Restart**: unless-stopped

### PostgreSQL Service
- **Image**: postgres:15-alpine
- **Port**: 5432
- **Health Check**: pg_isready
- **Network**: nexusforge-network
- **Volumes**: postgres_data:/var/lib/postgresql/data

### Redis Service
- **Image**: redis:7-alpine
- **Port**: 6379
- **Health Check**: redis-cli ping
- **Network**: nexusforge-network
- **Volumes**: redis_data:/data

### Migrations Service
- **Image**: Built from Dockerfile
- **Command**: alembic upgrade head
- **Depends**: postgres (healthy), redis (healthy)
- **Network**: nexusforge-network
- **Volumes**: ./backend/app:/app/app
- **Restart**: no

## Network
- **Name**: nexusforge-network
- **Driver**: bridge

## Volumes
- **postgres_data**: PostgreSQL data persistence
- **redis_data**: Redis data persistence

## Docker Compose Commands
```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Stop and remove volumes (clean state)
docker compose down -v

# View service logs
docker compose logs

# View specific service logs
docker compose logs backend
docker compose logs worker

# Check service status
docker compose ps

# Rebuild services
docker compose build --no-cache
docker compose up -d

# Restart a specific service
docker compose restart backend

# Remove a stopped service
docker compose rm -f frontend
```

## Environment Variables
The docker-compose.yml uses environment variables from `.env`. 
See `.env.example` for all available variables.

Key environment variables:
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` - Database credentials
- `DATABASE_URL` - Full database connection URL
- `REDIS_URL` - Redis connection URL
- `SECRET_KEY`, `JWT_SECRET_KEY`, `ENCRYPTION_KEY` - Security keys
- `MAX_CONCURRENT_WORKERS` - Worker pool size (default: 2)

## Build Order
1. PostgreSQL (must be healthy)
2. Redis (must be healthy)
3. Migrations (depends on DB/Redis being healthy)
4. Backend (depends on migrations)
5. Worker (depends on backend)
6. Frontend (depends on backend)

## Health Checks
Each service has health checks defined in docker-compose.yml:
- **postgres**: `pg_isready -U postgres`
- **redis**: `redis-cli ping`
- **backend**: No explicit health check (relies on `/api/health` endpoint)
- **worker**: No explicit health check (relies on heartbeat)

## Notes
- Frontend service requires `Dockerfile.frontend` to be created
- All services share the `nexusforge-network` network
- Data persists across restarts via named volumes
- Use `docker compose down -v` to completely reset data