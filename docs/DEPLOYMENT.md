# NexusForge Deployment Guide

## Prerequisites

### Required
- **Ubuntu 20.04 LTS** (or later)
- **Docker** v20.10+
- **Docker Compose** v2 (or v1)
- **Git**
- **Python 3.11+** (for development/testing)

### Install Docker
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

### Install Docker Compose
```bash
sudo apt-get update && sudo apt-get install -y docker-compose
```

## Configuration

### Environment Variables
Copy `.env.example` to `.env` and configure:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `postgresql://postgres:postgres@postgres:5432/nexusforge` | PostgreSQL connection URL |
| `REDIS_URL` | Yes | `redis://redis:6379/0` | Redis connection URL |
| `MAX_CONCURRENT_WORKERS` | No | `2` | Max concurrent worker tasks |
| `JWT_SECRET_KEY` | Yes | `test-secret-key-32-chars-long-enough-for-hs256` | JWT signing key (HS256) |
| `SECRET_KEY` | Yes | `test-secret-key-32-chars-long-enough` | Application secret |
| `ENCRYPTION_KEY` | Yes | `test-encryption-key-32-bytes-base64-c3RhY2xl` | Data encryption key |

### Generate Secure Keys
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Initial Deployment

### 1. Clone Repository
```bash
git clone https://github.com/nexusforge/nexusforge.git
cd nexusforge
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your values
```

### 3. Start Services
```bash
docker-compose up -d
```

### 4. Verify Deployment
```bash
# Check all services
docker-compose ps

# Health check
curl http://localhost:8000/health

# Verify migrations
docker exec -it nexusforge-postgres-1 psql -U postgres -d nexusforge -c "\dt"
```

## Database Migration Workflow

### Apply Migrations
```bash
docker-compose exec migrations alembic upgrade head
```

### Rollback
```bash
docker-compose exec migrations alembic downgrade -1
```

### View Migration History
```bash
docker-compose exec migrations alembic history
```

### Check Current Revision
```bash
docker-compose exec migrations alembic current
```

## Upgrade Workflow

### 1. Pull Changes
```bash
git pull origin main
```

### 2. Apply New Migrations
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

### 3. Verify
```bash
docker-compose ps
curl http://localhost:8000/health
```

## Rollback Considerations

1. **Database Backup**: Always backup before migration:
   ```bash
   docker exec nexusforge-postgres-1 pg_dump -U postgres nexusforge > backup.sql
   ```

2. **Rollback Migration**: Use `alembic downgrade -1` to revert one revision

3. **Full Rollback**: Restore from backup and re-run migrations

## Backup Considerations

### Daily Backup
```bash
docker exec nexusforge-postgres-1 pg_dump -U postgres nexusforge | gzip > /backups/db-$(date +%Y%m%d).sql.gz
```

### Redis Backup
```bash
docker exec nexusforge-redis-1 redis-cli save
```

## Worker Scaling

### Horizontal Scaling
```bash
docker-compose up -d --scale worker=3
```

### Configuration
- `MAX_CONCURRENT_WORKERS` controls tasks per worker
- Redis handles task queue distribution
- PostgreSQL tracks task state

## Troubleshooting

### Services Not Starting
```bash
docker-compose logs
```

### Database Connection Issues
```bash
docker exec nexusforge-postgres-1 pg_isready -U postgres
```

### Worker Not Claiming Tasks
```bash
docker-compose logs worker
```

## Production Notes

- **Secrets**: Use environment variables, never commit to git
- **TLS**: Configure nginx/reverse proxy for HTTPS
- **Monitoring**: Use Docker logs + external monitoring
- **Scaling**: Scale backend horizontally, worker vertically or horizontally