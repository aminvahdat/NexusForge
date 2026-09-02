# SYSTEM_ARCHITECTURE.md

## Overview

NexusForge is a modular, multi-tiered system designed for self-hosted AI agent orchestration. The architecture follows clean separation of concerns while maintaining flexibility for future scaling.

## Technology Stack

### Frontend
- **Framework**: React + TypeScript
- **Build**: Vite
- **Styling**: Tailwind CSS with custom design system
- **State Management**: Zustand (minimal local state)
- **Routing**: React Router
- **HTTP Client**: Axios (with interceptor-based auth handling)
- **Charts/Visualization**: D3.js for custom agent visualizations
- **Icons**: Lucide React

### Backend
- **Framework**: Python + FastAPI
- **Runtime**: asyncio-based, async/await throughout
- **Database**: PostgreSQL (primary), Redis (task queue, caching)
- **ORM**: SQLAlchemy (declarative models with async session)
- **Validation**: Pydantic v2
- **Dependency Injection**: FastAPI DI (custom dependencies for services)
- **WebSocket**: FastAPI WebSocket (asyncio)
- **Authentication**: JWT + bcrypt password hashing
- **Authorization**: RBAC via middleware
- **Queue**: Redis-backed task queue (Celery alternative)
- **Logging**: structlog (contextual logging with trace IDs)
- **Configuration**: Pydantic settings with .env loading
- **Serialization**: Pydantic models for all API schemas
- **Testing**: pytest with FastAPI TestClient
- **Containerization**: Docker + Docker Compose

### Worker Runtime
- **Framework**: Hermes Agent with abstraction layer
- **Language**: Python (tool execution, process management)
- **Interface**: Agent Runtime Interface (abstracts runtime-specific logic)
- **Communication**: REST API + WebSocket (task assignment, status updates)
- **Isolation**: Project-specific workspaces with context minimization

### Infrastructure
- **Deployment**: Docker Compose (Ubuntu 22.04 LTS recommended)
- **Service Discovery**: Service names in docker-compose.yml
- **Secrets**: Environment variables + optional external secret stores (Bitwarden, 1Password)
- **Monitoring**: Prometheus metrics via FastAPI middleware
- **Backup**: PostgreSQL dumps + Redis snapshots
- **Health Checks**: HTTP endpoints per service

## Component Layers

### 1. Presentation Layer (Frontend)
**Location**: `/frontend/src/`
**Responsibilities**: UI components, user interactions, real-time updates, notifications

#### Key Components
- **Dashboard** (`/frontend/src/pages/Dashboard/`): Project overview, metrics, activity feed
- **Projects List** (`/frontend/src/pages/Projects/`): Project management, filtering, sorting
- **Project Workspace** (`/frontend/src/pages/Project/`): Task graph, artifacts, logs, security reports
- **Agent Visualization** (`/frontend/src/components/AgentCluster/`): Animated role/worker visualization
- **Approval Center** (`/frontend/src/components/ApprovalCenter/`): Dangerous operation approval UI
- **Settings** (`/frontend/src/pages/Settings/`): User profile, AI providers, notifications

#### Technologies
- React 18+ hooks and concurrent rendering
- TypeScript for type safety
- Zustand for global state management
- WebSocket integration for real-time updates
- Responsive design with Tailwind CSS
- Accessibility compliance (WCAG 2.1)

### 2. API Layer (Backend - FastAPI)
**Location**: `/backend/app/api/`
**Responsibilities**: HTTP/REST endpoints, WebSocket handlers, request/response validation

#### Key Services
- **Auth Service** (`/backend/app/api/auth/`): Registration, login, logout, token management
- **Project Service** (`/backend/app/api/project/`): Project CRUD, workspace management
- **Task Service** (`/backend/app/api/task/`): Task lifecycle, dependency resolution, scheduling
- **Agent Service** (`/backend/app/api/agent/`): Role management, worker coordination
- **Approval Service** (`/backend/app/api/approval/`): Human approval workflows
- **Notification Service** (`/backend/app/api/notification/`): In-app and external notifications
- **Real-time Service** (`/backend/app/api/websocket/`): WebSocket connection management
- **Health Service** (`/backend/app/api/health/`): System health checks

#### Security
- JWT bearer authentication with refresh tokens
- Role-based access control (Admin/User)
- Input validation via Pydantic
- Rate limiting on authentication endpoints
- CORS configuration per environment
- HTTPS enforcement in production

### 3. Business Logic Layer (Services)
**Location**: `/backend/app/services/`
**Responsibilities**: Core business logic, data transformation, orchestration workflows

#### Key Services
- **Project Service**: Project lifecycle management, milestone tracking
- **Task Service**: Task decomposition, dependency resolution, parallel execution scheduling
- **Agent Service**: Role assignment, worker lifecycle management, skill loading
- **Security Service**: Security reviews, dependency scanning, deployment hardening
- **Approval Service**: Approval workflow management, risk assessment
- **Realtime Service**: Event streaming, activity broadcasting, status updates

### 4. Data Access Layer (Database & Persistence)
**Location**: `/backend/app/db/`
**Responsibilities**: Data storage, retrieval, persistence concerns

#### Database Schema
```sql
-- projects table: Project metadata
id (PK), name, description, status, created_by, created_at, updated_at, ...

-- tasks table: Task management
id (PK), project_id (FK), title, description, dependencies (JSON), assigned_role, 
required_skills (JSON), priority, status, worker_id (FK), created_at, ...

-- workers table: Worker management
id (PK), role, status, current_task_id (FK), skills (JSON), memory (JSON), ...

-- artifacts table: Artifact storage
id (PK), project_id (FK), type, title, content (JSON), author, created_at, ...

-- project_memory table: Project-specific knowledge
id (PK), project_id (FK), scope, key, value (JSON), created_at, ...

-- user_memory table: User preferences
id (PK), user_id (FK), key, value (JSON), created_at, ...

-- system_memory table: Global knowledge
id (PK), key, value (JSON), created_at, ...

-- approval_requests table: Human approval workflow
id (PK), task_id (FK), requested_by, action, reason, risk_level, status, ...

-- notifications table: Notification system
id (PK), user_id (FK), type, message, payload (JSON), sent_at, read_at, ...

-- sessions table: Authentication sessions
session_id (PK), user_id (FK), token, expires_at, created_at, ...
```

#### Redis Integration
- **Task Queue**: Redis list for pending tasks, worker assignments
- **Pub/Sub**: Real-time event broadcasting
- **Caching**: Task statuses, project data, user sessions
- **Locking**: Worker coordination, distributed locks

### 5. Runtime Adapter Layer
**Location**: `/backend/app/runtimes/`
**Responsibilities**: Abstraction layer for different AI agent runtimes

#### Component Structure
```
/src/runtimes/
├── base/
│   └── base.py           # Abstract RuntimeInterface
├── hermes/
│   └── hermes_adapter.py # Hermes Agent runtime implementation
└── plugins/              # Future runtime adapters (if needed)
```

#### Interface Definition
```python
class AgentRuntimeInterface:
    async def execute_task(self, task_spec: TaskSpecification) -> TaskResult:
        """Execute a single task with given specification."""

    async def assign_role(self, worker_id: str, role: AgentRole) -> bool:
        """Assign a logical role to a worker."""

    async def load_skills(self, worker_id: str, skill_names: List[str]) -> bool:
        """Load required skills for a worker."""

    async def get_worker_status(self, worker_id: str) -> WorkerStatus:
        """Get current status of a worker."""

    async def release_worker(self, worker_id: str, new_role: Optional[AgentRole] = None) -> bool:
        """Release worker back to pool, optionally with new role."""
```

### 6. Worker Pool Management
**Location**: `/backend/app/workers/pool/`
**Responsibilities**: Worker lifecycle, task distribution, resource management

#### Worker Architecture
- **Worker Processes**: Hermes instances spawned as subprocesses
- **Process Management**: asyncio subprocess management with health checks
- **Task Distribution**: Redis queue with worker assignments
- **Skill Management**: Dynamic skill loading based on assigned roles
- **Context Management**: Project-specific context injection

### 7. Memory Management
**Location**: `/backend/app/memory/`
**Responsibilities**: Multi-level memory storage and retrieval

#### Memory Architecture
```
/src/memory/
├── project/          # Project-specific knowledge
├── user/             # User-specific preferences
├── system/           # Global reusable knowledge
└── task/             # Short-lived task context
```

### 8. Artifact Management
**Location**: `/backend/app/artifacts/store/`
**Responsibilities**: Structured artifact storage and retrieval

#### Artifact Types
- **Requirements Documents**
- **Architecture Documents**
- **API Specifications**
- **Database Schemas**
- **Source Code**
- **Test Reports**
- **Security Reports**
- **Deployment Files**

## Data Flow Patterns

### 1. Task Execution Flow
```
User Request → Chief Orchestrator → Project Planner → Task Decomposition
    ↓                    ↓                    ↓                    ↓
Architect → Researcher → UI/UX Agent → Frontend Agent → Backend Agent
    ↓                                            ↓                    ↓
Database Agent → Security Agent → QA Agent → DevOps Agent
    ↓                    ↓                    ↓                    ↓
Integration → Testing → Deployment → Review → Delivery
```

### 2. Real-time Update Flow
```
User Action → Frontend WebSocket → API Gateway → Services → Redis Pub/Sub
    ↓
WebSocket Clients → Frontend Updates
```

### 3. Security Review Flow
```
Task Completion → Security Agent Review → Security Service Evaluation
    ↓
Generate Security Report → Artifact Storage → UI Display → Approval Required
```

## Security Boundaries

### 1. Process Isolation
- Each worker runs in a separate process (Hermes instance)
- Worker processes only have access to their project workspace
- Context isolation via containerization (future enhancement)

### 2. Network Isolation
- API Gateway authenticates all external requests
- Internal service communication via authenticated channels
- Workers communicate with API Gateway only

### 3. Data Access Controls
- RBAC at database level (row-level security)
- Workspace-based access control
- Secret management via environment variables

### 4. Permission Levels
- **SAFE**: Read project files, analyze code, read documentation
- **LIMITED**: Modify project workspace, run tests, install approved dependencies
- **PRIVILEGED**: Deployment operations, infrastructure configuration
- **DANGEROUS**: Destructive operations, root commands, production database operations

## Deployment Architecture

### 1. Docker Compose Configuration
```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - REACT_APP_API_URL=http://backend:8000

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/nexusforge
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./backend/app:/app

  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=nexusforge
      - POSTGRES_USER=postgres

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 2. Service Discovery
- Docker Compose service names used throughout the system
- Environment variables for service URLs
- Health checks for service availability

### 3. Configuration Management
- `.env` file for environment-specific configuration
- Pydantic settings classes for each environment
- Secret management via Docker secrets (production)
- Configuration hot-reload for non-production environments

## Scaling Considerations

### 1. Horizontal Scaling
- **Workers**: Add more worker containers via Docker swarm/Kubernetes (future)
- **Frontend**: Scale via load balancer or CDN
- **Database**: PostgreSQL read replicas, Redis clustering
- **API**: Scale via load balancer, maintain sticky sessions for sessions

### 2. Vertical Scaling
- **Frontend**: Increase container resources (CPU, memory)
- **Backend**: Database optimization, connection pooling
- **Workers**: Adjust worker count via `MAX_CONCURRENT_WORKERS`

### 3. Multi-server Deployment
```yaml
etc_hosts:
  backend: <backend_ip>
  postgres: <postgres_ip>
  redis: <redis_ip>
```

## Observability

### 1. Logging
- **Structured Logging**: structlog with trace IDs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Aggregation**: Log to JSON files, potentially to ELK stack
- **Log Rotation**: Automatic log rotation

### 2. Metrics
- **HTTP Metrics**: Request counts, response times, error rates
- **Task Metrics**: Task completion rates, worker utilization
- **System Metrics**: Resource usage (CPU, memory, disk, network)
- **Prometheus Integration**: For long-term monitoring

### 3. Tracing
- **Distributed Tracing**: Trace IDs across services
- **Span Correlation**: Correlate events across microservices
- **Jaeger Integration**: Future addition for distributed tracing

## Extensibility Points

### 1. Runtime Adapters
- New agent runtime implementations can be added as plugins
- Interface-based design allows for different runtimes

### 2. Agent Roles
- New logical agent roles can be defined without code changes
- Role definitions stored in database

### 3. Tools and Skills
- New toolsets can be registered and loaded dynamically
- Skills can be installed/uninstalled per worker

### 4. Authentication Providers
- Additional OAuth providers can be added
- Custom authentication mechanisms supported

## Performance Characteristics

| Component | Expected Load | Response Time | Throughput |
|-----------|---------------|---------------|------------|
| Frontend | 100 concurrent users | <100ms | 100+ req/sec |
| API Gateway | 50 concurrent users | <50ms | 200+ req/sec |
| Worker Pool | 2-10 workers | Task-dependent | Scalable |
| Database | 100+ concurrent connections | <10ms | 1000+ req/sec |
| Redis | 100+ concurrent connections | <1ms | 10000+ req/sec |

## Operational Considerations

### 1. Backup and Recovery
- PostgreSQL backups using pg_dump
- Redis snapshots for persistence
- Container image versioning
- Configuration management

### 2. Upgrades
- Docker Compose upgrade commands
- Database migration support
- Backward compatibility considerations

### 3. Troubleshooting
- Service health endpoints
- Log aggregation and analysis
- Performance monitoring
- Alerting configuration

## Future Enhancements

### 1. Multi-cloud Support
- Integration with cloud providers
- Hybrid deployment options

### 2. Advanced Features
- Auto-scaling based on workload
- Machine learning for optimization
- Automated security compliance

### 3. Integration
- Version control system integration
- Third-party service integrations
- Custom workflows

## Conclusion

This system architecture provides a solid foundation for NexusForge with:

1. **Clear Separation of Concerns**: Each layer has well-defined responsibilities
2. **Extensibility**: Plugin architecture allows for future enhancements
3. **Scalability**: Horizontal and vertical scaling options
4. **Security**: Multi-layered security controls
5. **Observability**: Comprehensive monitoring and logging
6. **Maintainability**: Clean code structure and documentation
7. **Testability**: Design facilitates unit and integration testing

The architecture balances current requirements with future flexibility, providing a platform that can evolve with the needs of users and the capabilities of AI agent systems.