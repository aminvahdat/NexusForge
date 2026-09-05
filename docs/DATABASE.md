# NexusForge Database Schema & Migration Guide

## Schema Overview

NexusForge uses PostgreSQL with SQLAlchemy ORM. All schema changes are managed via Alembic migrations.

## Tables

### Core Tables

#### `users`
User authentication and authorization.
```sql
id UUID PK
email VARCHAR(255) UNIQUE NOT NULL
username VARCHAR(50) UNIQUE
password_hash VARCHAR(255) NOT NULL
is_active BOOLEAN DEFAULT true
is_superuser BOOLEAN DEFAULT false
created_at TIMESTAMPTZ DEFAULT now()
updated_at TIMESTAMPTZ DEFAULT now()
last_login TIMESTAMPTZ
email_verified BOOLEAN DEFAULT false
verification_token VARCHAR(255)
verification_token_expires TIMESTAMPTZ
```
Indexes: `ix_users_email_lower`, `ix_users_created_at`

#### `projects`
Project containers for tasks and artifacts.
```sql
id UUID PK
owner_id UUID FK → users.id
name VARCHAR(255) NOT NULL
description TEXT
status VARCHAR(50) DEFAULT 'active'
created_at TIMESTAMPTZ DEFAULT now()
updated_at TIMESTAMPTZ DEFAULT now()
```
Indexes: `ix_projects_name`, `ix_projects_name_lower`, `ix_projects_owner_id`, `ix_projects_owner_created`, `ix_projects_status`

#### `tasks`
Task definitions assigned to workers.
```sql
id UUID PK
project_id UUID FK → projects.id
title VARCHAR(255) NOT NULL
description TEXT
role VARCHAR(50) -- agent role
status VARCHAR(50) DEFAULT 'queued'
priority INTEGER DEFAULT 0
required_skills JSON
dependencies JSON -- task IDs
input_artifacts JSON
output_artifacts JSON
assigned_worker_id UUID FK → workers.id
acceptance_criteria JSON
retry_count INTEGER DEFAULT 0
max_retries INTEGER DEFAULT 3
due_date TIMESTAMPTZ
created_at TIMESTAMPTZ DEFAULT now()
updated_at TIMESTAMPTZ DEFAULT now()
started_at TIMESTAMPTZ
completed_at TIMESTAMPTZ
estimated_tokens INTEGER
```
Indexes: `ix_tasks_assigned_worker_status`, `ix_tasks_created_at`, `ix_tasks_project_id`, `ix_tasks_project_status_created`, `ix_tasks_role_status`, `ix_tasks_status`

#### `workers`
Worker processes that execute tasks.
```sql
id UUID PK
worker_id VARCHAR(100) UNIQUE NOT NULL
hostname VARCHAR(255)
role VARCHAR(50)
status VARCHAR(50) DEFAULT 'idle'
current_task_id UUID FK → tasks.id
last_heartbeat TIMESTAMPTZ
created_at TIMESTAMPTZ DEFAULT now()
updated_at TIMESTAMPTZ DEFAULT now()
```
Indexes: `ix_workers_current_task_id`, `ix_workers_role_status`, `ix_workers_status`, `ix_workers_status_heartbeat`, `ix_workers_worker_id`

### Memory Tables

#### `user_memory`
Per-user key-value memory.
```sql
id UUID PK
user_id UUID FK → users.id
scope VARCHAR(50) NOT NULL
key VARCHAR(255) NOT NULL
value JSON NOT NULL
created_at TIMESTAMPTZ DEFAULT now()
updated_at TIMESTAMPTZ DEFAULT now()
```

#### `project_memory`
Per-project key-value memory.
```sql
id UUID PK
project_id UUID FK → projects.id
scope VARCHAR(50) NOT NULL
key VARCHAR(255) NOT NULL
value JSON NOT NULL
created_at TIMESTAMPTZ DEFAULT now()
updated_at TIMESTAMPTZ DEFAULT now()
```
Indexes: `ix_project_memory_project_scope`, `ix_project_memory_scope_key`

#### `system_memory`
Global system key-value memory.
```sql
id UUID PK
key VARCHAR(255) UNIQUE NOT NULL
value JSON NOT NULL
description TEXT
created_at TIMESTAMPTZ DEFAULT now()
updated_at TIMESTAMPTZ DEFAULT now()
created_by VARCHAR(100)
```

### Authentication & Security

#### `user_api_keys`
API keys for programmatic access.
```sql
id UUID PK
user_id UUID FK → users.id
provider VARCHAR(50) NOT NULL
key_hash VARCHAR(255) NOT NULL
name VARCHAR(100)
is_active BOOLEAN DEFAULT true
created_at TIMESTAMPTZ DEFAULT now()
last_used_at TIMESTAMPTZ
expires_at TIMESTAMPTZ
```
Indexes: `ix_user_api_keys_user_id`, `ix_user_api_keys_user_provider`

#### `approval_requests`
Approval workflow for sensitive operations.
```sql
id UUID PK
task_id UUID FK → tasks.id
requested_by_user_id UUID FK → users.id
approved_by_user_id UUID FK → users.id
status VARCHAR(50) DEFAULT 'pending'
request_data JSON
approval_data JSON
requested_at TIMESTAMPTZ DEFAULT now()
responded_at TIMESTAMPTZ
```
Indexes: `ix_approval_requests_requested_at`, `ix_approval_requests_requested_by_user_id`, `ix_approval_requests_status`, `ix_approval_requests_task_id`

### Artifacts & Events

#### `artifacts`
Generated files from task execution.
```sql
id UUID PK
project_id UUID FK → projects.id
task_id UUID FK → tasks.id
author_id UUID FK → users.id
type VARCHAR(50) NOT NULL -- code, test, doc, log, etc.
name VARCHAR(255) NOT NULL
path VARCHAR(500) NOT NULL
size_bytes INTEGER
checksum VARCHAR(64)
content_type VARCHAR(100)
metadata JSON
created_at TIMESTAMPTZ DEFAULT now()
```
Indexes: `ix_artifacts_author_created`, `ix_artifacts_author_id`, `ix_artifacts_project_id`, `ix_artifacts_project_type`, `ix_artifacts_task_created`, `ix_artifacts_task_id`

#### `events`
System event log.
```sql
id UUID PK
source VARCHAR(100) NOT NULL
type VARCHAR(100) NOT NULL
payload JSON
severity VARCHAR(20) DEFAULT 'info'
created_at TIMESTAMPTZ DEFAULT now()
```

#### `task_logs`
Detailed task execution logs.
```sql
id UUID PK
task_id UUID FK → tasks.id
worker_id UUID FK → workers.id
level VARCHAR(20) NOT NULL
message TEXT NOT NULL
context JSON
created_at TIMESTAMPTZ DEFAULT now()
```

#### `worker_logs`
Worker operation logs.
```sql
id UUID PK
worker_id UUID FK → workers.id
level VARCHAR(50) NOT NULL
message TEXT NOT NULL
context JSON
created_at TIMESTAMPTZ DEFAULT now()
```
Indexes: `ix_worker_logs_created_at`, `ix_worker_logs_worker_id`

### Notification Tables

#### `notifications`
User notifications.
```sql
id UUID PK
user_id UUID FK → users.id
type VARCHAR(50) NOT NULL
title VARCHAR(255)
message TEXT
data JSON
is_read BOOLEAN DEFAULT false
created_at TIMESTAMPTZ DEFAULT now()
```
Indexes: `ix_notifications_created_at`, `ix_notifications_user_id`

## Migration Workflow

### Generate New Migration
```bash
# From repository root
alembic revision --autogenerate -m "description"
```

### Apply Migrations
```bash
alembic upgrade head
```

### Rollback
```bash
alembic downgrade -1  # one step
alembic downgrade base  # all
```

### View Current State
```bash
alembic current
alembic history
```

## Production Database Setup

### Clean Database Creation
```bash
# Create fresh database
createdb -U postgres nexusforge

# Run migrations
alembic upgrade head
```

### Backup
```bash
pg_dump -U postgres nexusforge > backup.sql
pg_dump -U postgres --schema-only nexusforge > schema.sql
```

### Restore
```bash
psql -U postgres -d nexusforge < backup.sql
```

## Naming Conventions

All constraints follow PostgreSQL naming convention:
- Primary Keys: `pk_{table_name}`
- Foreign Keys: `fk_{table_name}_{column}_{referred_table}`
- Unique: `uq_{table_name}_{column}`
- Indexes: `ix_{table_name}_{column}`
- Check: `ck_{table_name}_{constraint}`

## Connection Pooling

Configured via SQLAlchemy:
- `pool_size`: 5
- `max_overflow`: 10
- `pool_timeout`: 30
- `pool_recycle`: 1800

## Security

- All passwords hashed with bcrypt
- API keys stored as SHA256 hashes
- Row-level security via `owner_id` FK
- Encryption keys stored in environment variables