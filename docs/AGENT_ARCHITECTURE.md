# AGENT_ARCHITECTURE.md

## Overview

NexusForge's agent architecture is designed around the fundamental principle that **Agent Roles are logical profiles, not permanent processes**. Workers are reusable execution resources that dynamically load logical agent roles to perform specific tasks.

## Core Concepts

### Agent Roles vs Workers

| Concept | Description | Lifetime | Example |
|---------|-------------|----------|---------|
| **Agent Role** | Logical expertise profile defining what a worker should know and do | Persistent (definition) | Frontend Agent, Security Engineer |
| **Worker** | Physical execution resource (Hermes instance) that performs tasks | Transient (spawned/destroyed) | Worker 1, Worker 2, Worker N |

### Key Principles

1. **No Permanent One-to-One Mapping**: Do not create a permanent Hermes instance for every agent role
2. **Dynamic Role Loading**: Workers receive role definitions at task assignment time
3. **Context Minimization**: Workers receive only project-relevant context, not entire history
4. **Role Isolation**: Each worker execution is isolated from others
5. **Reusability**: After completing a task, workers return to the pool and can take on different roles

## Agent Role System

### Built-in Agent Roles

#### 1. Chief Orchestrator
**Responsibilities**:
- Understand user intent and analyze requirements
- Determine project type and select appropriate agent roles
- Delegate work and manage execution
- Monitor progress and resolve conflicts
- Decide when a project is complete

#### 2. Project Planner
**Responsibilities**:
- Requirements analysis and PRD generation
- User stories and acceptance criteria
- Milestone creation and dependency identification
- Task decomposition and effort estimation

#### 3. Software Architect
**Responsibilities**:
- Technology selection and system architecture design
- API architecture and database architecture
- Integration architecture and scalability planning
- Architectural decision records (ADRs)

#### 4. Research Agent
**Responsibilities**:
- Research official documentation and validate APIs
- Compare technologies and investigate compatibility
- Provide evidence-based recommendations
- Prohibit unsupported technical assumptions

#### 5. UI/UX Agent
**Responsibilities**:
- User flows and information architecture
- Responsive design and design systems
- UX review and accessibility compliance
- Component library recommendations

#### 6. Frontend Agent
**Responsibilities**:
- Frontend implementation and component creation
- State management and API integration
- Responsive UI and cross-browser compatibility
- Testing (unit, integration, visual regression)

#### 7. Backend Agent
**Responsibilities**:
- API development and business logic implementation
- Integrations and background job processing
- Data validation and error handling
- Performance optimization and testing

#### 8. Mobile Agent
**Responsibilities**:
- iOS/Android development (Swift, Kotlin, React Native, Flutter)
- Cross-platform development framework selection
- Mobile-specific performance and UI/UX considerations
- App store deployment preparation

#### 9. Database Agent
**Responsibilities**:
- Data model design and schema creation
- Migration strategy and index optimization
- Data integrity constraints and performance tuning
- Backup and recovery planning

#### 10. Security Agent
**Responsibilities**:
- Authentication and authorization review
- RBAC implementation and API security
- Input validation and secret management
- Dependency review and OWASP-oriented assessment
- Deployment hardening and penetration testing guidance

#### 11. QA Agent
**Responsibilities**:
- Unit, integration, and end-to-end test creation
- Regression testing and bug reporting
- Test automation and verification
- Quality gate enforcement

#### 12. DevOps Agent
**Responsibilities**:
- Docker and Docker Compose configuration
- CI/CD pipeline preparation and environment configuration
- Logging and monitoring setup
- Deployment scripts and infrastructure as code

### Dynamic Temporary Roles

The Orchestrator can create temporary logical roles when necessary:

- **Smart Home Engineer** (for home automation projects)
- **IoT Engineer** (for sensor/actuator systems)
- **MQTT Specialist** (for messaging protocols)
- **Home Assistant Integration Specialist**
- **Zigbee Specialist** (for wireless protocols)
- **Network Automation Engineer**
- **Computer Vision Engineer**
- **Machine Learning Engineer**
- **Payment Integration Specialist**
- **Blockchain Developer**
- **AR/VR Developer**
- **Game Developer**

**Temporary Role Requirements**:
- Clear purpose and defined scope
- Restricted permissions (least privilege)
- Relevant skills pre-loaded
- Project association
- Automatic removal after completion

## Agent Runtime Abstraction Layer

### Interface Definition

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AgentRole(str, Enum):
    """Predefined logical agent roles."""
    CHIEF_ORCHESTRATOR = "chief_orchestrator"
    PROJECT_PLANNER = "project_planner"
    SOFTWARE_ARCHITECT = "software_architect"
    RESEARCH_AGENT = "research_agent"
    UI_UX_AGENT = "ui_ux_agent"
    FRONTEND_AGENT = "frontend_agent"
    BACKEND_AGENT = "backend_agent"
    MOBILE_AGENT = "mobile_agent"
    DATABASE_AGENT = "database_agent"
    SECURITY_AGENT = "security_agent"
    QA_AGENT = "qa_agent"
    DEVOPS_AGENT = "devops_agent"


class TaskSpecification:
    def __init__(self, task_id: str, role: AgentRole, description: str,
                 required_skills: List[str], context: Dict[str, Any],
                 input_artifacts: List[str], tool_permissions: List[str]):
        self.task_id = task_id
        self.role = role
        self.description = description
        self.required_skills = required_skills
        self.context = context
        self.input_artifacts = input_artifacts
        self.tool_permissions = tool_permissions


class TaskResult:
    def __init__(self, task_id: str, status: str, output: Any = None,
                 artifacts: List[str] = None, error: str = None,
                 execution_time: float = 0.0):
        self.task_id = task_id
        self.status = status  # completed, failed, blocked, needs_revision
        self.output = output
        self.artifacts = artifacts or []
        self.error = error
        self.execution_time = execution_time


class WorkerStatus:
    def __init__(self, worker_id: str, status: str, current_task: Optional[str] = None,
                 current_role: Optional[AgentRole] = None, skills: List[str] = None):
        self.worker_id = worker_id
        self.status = status  # idle, busy, error, offline
        self.current_task = current_task
        self.current_role = current_role
        self.skills = skills or []


class AgentRuntimeInterface(ABC):
    """Abstract interface for agent runtime implementations."""

    @abstractmethod
    async def execute_task(self, task_spec: TaskSpecification) -> TaskResult:
        """Execute a single task with the given specification."""

    @abstractmethod
    async def assign_role(self, worker_id: str, role: AgentRole) -> bool:
        """Assign a logical role to a worker."""

    @abstractmethod
    async def load_skills(self, worker_id: str, skill_names: List[str]) -> bool:
        """Load required skills for a worker."""

    @abstractmethod
    async def get_worker_status(self, worker_id: str) -> WorkerStatus:
        """Get current status of a worker."""

    @abstractmethod
    async def release_worker(self, worker_id: str,
                           new_role: Optional[AgentRole] = None) -> bool:
        """Release worker back to pool, optionally with new role."""
```

### Hermes Runtime Adapter

The first implementation adapts the AgentRuntimeInterface to Hermes Agent capabilities:

```python
import asyncio
import json
import os
import subprocess
import tempfile
import uuid
from typing import List, Optional, Dict, Any
from pathlib import Path
from .base import AgentRuntimeInterface, TaskSpecification, TaskResult, WorkerStatus, AgentRole


class HermesRuntimeAdapter(AgentRuntimeInterface):
    """Hermes Agent implementation of the runtime interface."""

    def __init__(self, hermes_binary: str = "hermes",
                 workspace_root: str = "./workspace",
                 max_concurrent_tasks: int = 5):
        self.hermes_binary = hermes_binary
        self.workspace_root = Path(workspace_root)
        self.max_concurrent_tasks = max_concurrent_tasks
        self.active_workers: Dict[str, Dict] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()

    async def execute_task(self, task_spec: TaskSpecification) -> TaskResult:
        """Execute a task using Hermes Agent."""
        start_time = asyncio.get_event_loop().time()
        worker_id = f"worker-{uuid.uuid4().hex[:8]}"
        
        try:
            # Create isolated workspace for this task
            task_workspace = self.workspace_root / worker_id
            task_workspace.mkdir(parents=True, exist_ok=True)
            
            # Prepare task context
            context_file = task_workspace / "context.json"
            with open(context_file, 'w') as f:
                json.dump({
                    "task_description": task_spec.description,
                    "role": task_spec.role.value,
                    "required_skills": task_spec.required_skills,
                    "context": task_spec.context,
                    "input_artifacts": task_spec.input_artifacts
                }, f, indent=2)
            
            # Build Hermes command with appropriate toolsets
            cmd = [
                self.hermes_binary,
                "chat",
                "-q", f"Execute task: {task_spec.description}",
                "--skills", ",".join(task_spec.required_skills),
                "--workspace", str(task_workspace),
                "--context-file", str(context_file)
            ]
            
            # Execute task (this would be enhanced with actual Hermes integration)
            # For now, simulate the execution
            await asyncio.sleep(2)  # Placeholder for actual Hermes execution
            
            # Simulate successful completion
            result = TaskResult(
                task_id=task_spec.task_id,
                status="completed",
                output=f"Task {task_spec.task_id} completed by {task_spec.role.value}",
                artifacts=[f"{task_spec.task_id}-output.md"],
                execution_time=asyncio.get_event_loop().time() - start_time
            )
            
            return result
            
        except Exception as e:
            return TaskResult(
                task_id=task_spec.task_id,
                status="failed",
                error=str(e),
                execution_time=asyncio.get_event_loop().time() - start_time
            )
        finally:
            # Cleanup workspace (optional - could keep for debugging)
            # shutil.rmtree(task_workspace, ignore_errors=True)
            pass

    async def assign_role(self, worker_id: str, role: AgentRole) -> bool:
        """Assign a role to a worker (Hermes-specific implementation)."""
        if worker_id not in self.active_workers:
            self.active_workers[worker_id] = {}
        
        self.active_workers[worker_id]["role"] = role.value
        self.active_workers[worker_id]["assigned_at"] = asyncio.get_event_loop().time()
        return True

    async def load_skills(self, worker_id: str, skill_names: List[str]) -> bool:
        """Load skills for a worker."""
        if worker_id not in self.active_workers:
            self.active_workers[worker_id] = {}
        
        self.active_workers[worker_id]["skills"] = skill_names
        self.active_workers[worker_id]["skills_loaded_at"] = asyncio.get_event_loop().time()
        return True

    async def get_worker_status(self, worker_id: str) -> WorkerStatus:
        """Get current status of a worker."""
        if worker_id not in self.active_workers:
            return WorkerStatus(
                worker_id=worker_id,
                status="offline"
            )
        
        worker_info = self.active_workers[worker_id]
        return WorkerStatus(
            worker_id=worker_id,
            status=worker_info.get("status", "idle"),
            current_task=worker_info.get("current_task"),
            current_role=AgentRole(worker_info["role"]) if "role" in worker_info else None,
            skills=worker_info.get("skills", [])
        )

    async def release_worker(self, worker_id: str,
                           new_role: Optional[AgentRole] = None) -> bool:
        """Release worker back to pool."""
        if worker_id in self.active_workers:
            if new_role:
                self.active_workers[worker_id]["role"] = new_role.value
                self.active_workers[worker_id]["released_at"] = asyncio.get_event_loop().time()
            else:
                # Remove worker from active pool
                del self.active_workers[worker_id]
        return True
```

### Worker Lifecycle Management

#### 1. Worker Initialization
- Workers are spawned as Hermes subprocesses
- Each worker gets an isolated workspace
- Initial state: idle, no role assigned

#### 2. Role Assignment
- When a task is queued, Orchestrator selects appropriate role
- Worker receives role definition via `assign_role()`
- Required skills are loaded via `load_skills()`

#### 3. Task Execution
- Worker executes task via `execute_task()`
- Receives TaskSpecification with context and permissions
- Returns TaskResult with output and any generated artifacts

#### 4. Worker Release
- After task completion, worker returns to pool
- Can be assigned same or different role
- Context from previous task is cleared (security isolation)

## Communication Patterns

### 1. Orchestrator → Worker
```
Orchestrator creates TaskSpecification → 
Calls runtime.assign_role() → 
Calls runtime.load_skills() → 
Calls runtime.execute_task()
```

### 2. Worker → Orchestrator
```
Worker executes task → 
Returns TaskResult → 
Orchestrator updates task status → 
Triggers dependent tasks if completed
```

### 3. Real-time Updates
```
Task status change → 
Published to Redis pub/sub → 
WebSocket clients receive update → 
Frontend updates UI in real-time
```

## Context Management

### Context Scopes
1. **System Memory**: Global knowledge accessible to all workers
2. **User Memory**: User-specific preferences and settings
3. **Project Memory**: Project-specific knowledge (architecture decisions, requirements)
4. **Task Context**: Short-lived context specific to current task execution

### Context Injection
- Workers receive only relevant project context
- No worker receives entire conversation history
- Context is minimized to reduce token usage and improve focus
- Sensitive data is filtered based on role permissions

## Skill Management

### Skill Loading Process
1. Orchestrator determines required skills for task
2. Runtime loads skills via Hermes skill system
3. Skills are isolated to worker's execution context
4. Skills are unloaded when worker is released (optional)

### Skill Types
- **Core Skills**: Built into Hermes (web search, terminal, file operations)
- **Domain Skills**: Specific to agent roles (security-scanning, ui-design, etc.)
- **Project Skills**: Project-specific skills loaded from workspace
- **Temporary Skills**: Task-specific skills loaded on demand

## Security Model

### Tool Permission Levels
- **SAFE**: Read-only operations (read files, search, analyze)
- **LIMITED**: Modification operations (write files, run tests, install deps)
- **PRIVILEGED**: Infrastructure operations (deployment, config changes)
- **DANGEROUS**: Destructive operations (require explicit approval)

### Permission Enforcement
- Each worker gets tool permissions based on assigned role
- Dangerous operations require human approval via Approval Center
- Workers cannot exceed their permission boundaries
- Audit logs track all tool usage by worker and role

## Data Flow Example: Building a Web Application

```
1. User: "Build a task management SaaS"
2. Chief Orchestrator: Analyzes request, selects roles
3. Project Planner: Creates requirements, user stories, milestones
4. Software Architect: Chooses React + Node.js + PostgreSQL stack
5. UI/UX Agent: Designs user flows, wireframes, component library
6. Frontend Agent: Implements React components, state management
7. Backend Agent: Builds REST API, authentication, database models
8. Database Agent: Designs schema, indexes, migrations
9. Security Agent: Reviews auth, validation, dependencies, OWASP
10. QA Agent: Creates unit/integration tests, test automation
11. DevOps Agent: Creates Dockerfile, docker-compose, deployment scripts
12. Orchestrator: Coordinates, monitors, resolves blockers
13. Final Output: Complete, tested, secure application ready for deployment
```

Each step involves:
- Role assignment to available worker
- Skill loading for that role
- Context injection (relevant project info)
- Task execution
- Artifact generation (requirements, designs, code, tests)
- Status updates and notifications

## Implementation Notes

### Hermes-Specific Adaptations
- Uses `hermes chat -q` for one-shot task execution
- Leverages Hermes skill system for domain-specific capabilities
- Uses Hermes workspace isolation for security
- Integrates with Hermes memory system for persistence
- Utilizes Hermes tool permission system for security boundaries

### Future Extensibility
- Interface-based design allows adding new runtime adapters
- New agent roles can be added without changing core logic
- Skill system allows for domain-specific capability extension
- Plugin architecture enables custom functionality

## Conclusion

This agent architecture provides:

1. **Clear Separation**: Agent roles (logical) vs workers (physical)
2. **Flexibility**: Dynamic role assignment and worker reuse
3. **Security**: Context minimization and permission boundaries
4. **Scalability**: Configurable worker pool with horizontal scaling potential
5. **Extensibility**: Interface-based runtime adapter system
6. **Observability**: Clear task lifecycle and status tracking
7. **Maintainability**: Modular design with well-defined responsibilities

The architecture successfully implements the core principle from the NexusForge specification: **Agent Roles are not Workers**, enabling a truly flexible and reusable AI agent orchestration platform.