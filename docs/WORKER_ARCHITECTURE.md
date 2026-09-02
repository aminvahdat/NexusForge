# WORKER_ARCHITECTURE.md

## Overview

NexusForge's worker architecture implements a **configurable worker pool** that provides the execution resources for the logical agent roles. Workers are not permanently bound to roles; they are reusable execution resources that dynamically load agent roles as needed.

## Core Principles

1. **Workers = Execution Resources, Roles = Logical Profiles**
   - Workers are physical processes (Hermes instances)
   - Roles are logical expertise profiles defining what a worker should know and do
   - Workers dynamically load roles at task assignment time

2. **Reusability and Flexibility**
   - Workers return to the pool after task completion
   - Workers can take on different roles over time
   - No permanent one-to-one mapping between workers and roles

3. **Scalability and Isolation**
   - Configurable worker pool size based on resources
   - Each worker operates in its own isolated environment
   - Context isolation prevents contamination between tasks

## Worker Architecture Overview

### Worker Pool Structure
```
+------------------------+
|    Chief Orchestrator   |
+------------------------+
         |
         v
+------------------------+
|   Task Scheduler        |
+------------------------+
         |
         v
+------------------------+
|   Task Queue           |
+------------------------+
         |
    |         |
    v         v
Worker 1    Worker 2    Worker N
(Hermes)   (Hermes)   (Hermes)
|           |           |
+-----------+-----------+---------------
| Logical Agent Roles |
| (Frontend)         |
| (Backend)          |
| (Security)         |
| (QA)              |
+-------------------+
```

### Worker Components

#### 1. Worker Process
- **Runtime**: Hermes Agent instance
- **Isolation**: Process-level isolation
- **Workspace**: Temporary directory for task execution
- **Resources**: CPU, memory, permissions scoped to the worker

#### 2. Role Definition
- **Storage**: Role definitions stored in database
- **Skills**: Associated skills and capabilities
- **Permissions**: Tool permission levels based on role
- **Context**: Default context and system instructions

#### 3. Task Assignment
- **Queue**: Task queue managed by scheduler
- **Assignment**: Role and task details sent to worker
- **Context**: Project-relevant context and inputs
- **Permissions**: Tool permissions for the specific task

## Worker Lifecycle

### Phase 1: Worker Pool Initialization

#### Worker Pool Creation
```python
class WorkerPool:
    def __init__(self, config: WorkerPoolConfig):
        self.config = config
        self.workers: Dict[str, HermesWorker] = {}
        self.available_workers: Queue[str] = Queue()
        self.busy_workers: Set[str] = set()
        self.max_concurrent = config.max_concurrent_workers

    async def initialize_workers(self):
        for i in range(self.max_concurrent):
            worker_id = f"worker-{i}"
            worker = await HermesWorker.create(worker_id, self.config)
            self.workers[worker_id] = worker
            self.available_workers.put(worker_id)
```

#### Worker Configuration
- **Worker Type**: Hermes Worker with configurable capabilities
- **Resource Limits**: CPU, memory, time constraints
- **Tool Permissions**: Default SAFE permissions
- **Workspace**: Root workspace with subdirectories
- **Cleanup**: Automatic cleanup after task completion

### Phase 2: Worker Assignment and Execution

#### Worker Assignment Logic
```python
class TaskScheduler:
    def __init__(self, worker_pool: WorkerPool, task_queue: TaskQueue):
        self.worker_pool = worker_pool
        self.task_queue = task_queue

    async def assign_tasks(self):
        while not self.task_queue.is_empty():
            if len(self.worker_pool.busy_workers) >= self.worker_pool.max_concurrent:
                await asyncio.sleep(0.1)  # Wait for available workers
                continue

            task = await self.task_queue.get_next_task()
            worker_id = await self.worker_pool.get_available_worker()

            if worker_id:
                await self._assign_task_to_worker(worker_id, task)
```

#### Task Assignment Process
1. **Role Selection**: Based on task requirements and available workers
2. **Worker Selection**: From available worker pool
3. **Context Preparation**: Relevant project context and inputs
4. **Skill Loading**: Required skills for the assigned role
5. **Task Dispatch**: Task details sent to worker

### Phase 3: Worker Execution

#### Worker Execution Model
```python
class HermesWorker:
    async def execute_task(self, task_spec: TaskSpecification) -> TaskResult:
        """Execute a task with dynamic role loading."""

        # Phase 1: Role and Skill Loading
        await self._load_role(task_spec.role)
        await self._load_skills(task_spec.required_skills)

        # Phase 2: Context Injection
        await self._setup_workspace(task_spec)
        await self._prepare_context(task_spec.context)

        # Phase 3: Task Execution
        start_time = time.time()
        try:
            # Execute Hermes command
            result = await self._run_hermes_command(task_spec)

            # Phase 4: Result Processing
            await self._store_artifacts(result.artifacts)
            await self._cleanup_context()

            return TaskResult(
                task_id=task_spec.task_id,
                status="completed",
                output=result.output,
                artifacts=result.artifacts,
                execution_time=time.time() - start_time
            )
        except Exception as e:
            # Handle failure
            await self._handle_failure(e)
            return TaskResult(
                task_id=task_spec.task_id,
                status="failed",
                error=str(e),
                execution_time=time.time() - start_time
            )
```

### Phase 4: Worker Release and Pool Management

#### Worker Release Process
```python
class WorkerPool:
    async def release_worker(self, worker_id: str, new_role: Optional[AgentRole] = None):
        """Release worker back to pool with optional new role."""

        worker = self.workers.get(worker_id)
        if not worker:
            return False

        # Clean up task-specific context
        await worker._cleanup_task_context()

        # Clear role if not specified
        if new_role:
            await worker._assign_role(new_role)
        else:
            await worker._clear_role()

        # Return to available pool
        self.busy_workers.discard(worker_id)
        self.available_workers.put(worker_id)

        return True
```

## Worker Configuration

### Worker Pool Configuration
```yaml
worker_pool:
  # Maximum concurrent workers
  max_concurrent_workers: 2

  # Worker configuration template
  worker_template:
    # Worker type and runtime
    type: hermes
    runtime: hermes-agent

    # Resource limits
    resources:
      cpu_limit: 2.0  # CPU cores
      memory_limit: 4096  # MB
      timeout: 3600  # seconds

    # Tool permissions
    permissions:
      default_level: "SAFE"
      role_overrides:
        - role: "security_agent"
          level: "LIMITED"
        - role: "devops_agent"
          level: "PRIVILEGED"

    # Workspace configuration
    workspace:
      base_path: "/tmp/nexusforge-workspace"
      cleanup_policy: "after_task"
      max_workspace_size: 1073741824  # 1GB

    # Hermes configuration
    hermes:
      binary: "hermes"
      max_turns: 90
      toolsets: "web,terminal,file,code_execution,coding"
      worktree_mode: true
      profile: "worker-profile"

  # Worker lifecycle
  lifecycle:
    max_uptime: 86400  # seconds (24 hours)
    health_check_interval: 30  # seconds
    restart_on_failure: true
    restart_policy: "exponential_backoff"

  # Monitoring and metrics
  monitoring:
    metrics_enabled: true
    log_level: "INFO"
    metrics_port: 8080
    prometheus_endpoint: "/metrics"
```

### Role Configuration
```yaml
agent_roles:
  frontend_agent:
    name: "Frontend Agent"
    description: "Implements frontend applications using modern frameworks"
    skills:
      - "frontend_development"
      - "component_design"
      - "state_management"
      - "api_integration"
    permissions: "LIMITED"
    capabilities:
      - "react"
      - "vue"
      - "angular"
      - "typescript"
      - "tailwind"

  backend_agent:
    name: "Backend Agent"
    description: "Implements backend services and APIs"
    skills:
      - "backend_development"
      - "api_design"
      - "database_integration"
      - "authentication"
    permissions: "LIMITED"
    capabilities:
      - "python"
      - "fastapi"
      - "postgresql"
      - "docker"

  security_agent:
    name: "Security Agent"
    description: "Ensures security and compliance"
    skills:
      - "security_analysis"
      - "vulnerability_scanning"
      - "dependency_review"
      - "authorization"
    permissions: "LIMITED"
    capabilities:
      - "owasp_top_10"
      - "dependency_check"
      - "secret_scanning"

  qa_agent:
    name: "QA Agent"
    description: "Ensures quality and testing"
    skills:
      - "test_automation"
      - "test_design"
      - "bug_reporting"
      - "quality_gates"
    permissions: "SAFE"
    capabilities:
      - "pytest"
      - "jest"
      - "selenium"
      - "playwright"

  devops_agent:
    name: "DevOps Agent"
    description: "Manages deployment and infrastructure"
    skills:
      - "docker"
      - "ci_cd"
      - "infrastructure"
      - "monitoring"
    permissions: "PRIVILEGED"
    capabilities:
      - "docker_compose"
      - "github_actions"
      - "kubernetes"
      - "terraform"
```

## Worker Execution Model

### Task Execution Phases

#### Phase 1: Preparation
1. **Role Assignment**: Worker receives logical role definition
2. **Skill Loading**: Required skills loaded into worker
3. **Context Setup**: Project workspace and context prepared
4. **Tool Permissions**: Appropriate tool permissions activated

#### Phase 2: Execution
1. **Hermes Initialization**: Hermes process starts with role context
2. **Task Processing**: Hermes executes task via `hermes chat -q`
3. **Artifact Generation**: Task outputs and artifacts created
4. **Monitoring**: Task execution monitored for progress and errors

#### Phase 3: Cleanup and Release
1. **Result Processing**: Task results processed and stored
2. **Workspace Cleanup**: Task-specific workspace cleaned up
3. **Role Release**: Worker released from current role
4. **Pool Return**: Worker returned to available pool

### Task Specification Format
```python
class TaskSpecification:
    def __init__(self,
                 task_id: str,
                 role: AgentRole,
                 description: str,
                 required_skills: List[str],
                 context: Dict[str, Any],
                 input_artifacts: List[str],
                 tool_permissions: List[str],
                 dependencies: List[str] = None):
        self.task_id = task_id
        self.role = role
        self.description = description
        self.required_skills = required_skills
        self.context = context
        self.input_artifacts = input_artifacts
        self.tool_permissions = tool_permissions
        self.dependencies = dependencies or []
```

## Worker Pool Management

### Dynamic Scaling

#### Scaling Up
```python
class WorkerPoolManager:
    async def scale_up(self, additional_workers: int):
        """Scale up the worker pool."""
        current_count = len(self.worker_pool.workers)
        target_count = current_count + additional_workers

        while len(self.worker_pool.workers) < target_count:
            worker_id = f"worker-{len(self.worker_pool.workers)}"
            worker = await HermesWorker.create(worker_id, self.config)
            self.worker_pool.workers[worker_id] = worker
            self.worker_pool.available_workers.put(worker_id)

        # Update configuration
        self.config.max_concurrent_workers = target_count
        await self._update_configuration()
```

#### Scaling Down
```python
async def scale_down(self, worker_count: int):
    """Scale down the worker pool gracefully."""
    workers_to_remove = list(self.worker_pool.workers.keys())[:worker_count]

    for worker_id in workers_to_remove:
        # Cancel running tasks
        await self._cancel_worker_tasks(worker_id)

        # Clean up worker
        worker = self.worker_pool.workers.pop(worker_id)
        await worker.cleanup()

        # Remove from available/busy sets
        self.worker_pool.busy_workers.discard(worker_id)
        # (Note: busy workers will be removed when they finish current tasks)

    # Update configuration
    self.config.max_concurrent_workers = len(self.worker_pool.workers)
    await self._update_configuration()
```

### Worker Health Monitoring
```python
class WorkerMonitor:
    def __init__(self, worker_pool: WorkerPool):
        self.worker_pool = worker_pool
        self.health_check_interval = 30  # seconds
        self.health_check_timeout = 10   # seconds

    async def start_monitoring(self):
        """Start continuous worker health monitoring."""
        while True:
            await self._check_all_workers_health()
            await asyncio.sleep(self.health_check_interval)

    async def _check_all_workers_health(self):
        """Check health of all workers."""
        for worker_id, worker in self.worker_pool.workers.items():
            await self._check_worker_health(worker_id, worker)

    async def _check_worker_health(self, worker_id: str, worker: HermesWorker):
        """Check health of a specific worker."""
        try:
            # Check if worker process is alive
            is_alive = await worker.is_alive()

            if not is_alive:
                await self._handle_unhealthy_worker(worker_id, worker)
            else:
                # Get worker metrics
                metrics = await worker.get_metrics()

                # Check for resource exhaustion
                if metrics.cpu_usage > 0.9 or metrics.memory_usage > 0.9:
                    await self._handle_resource_exhaustion(worker_id, metrics)
                elif metrics.memory_usage > 0.7:
                    await self._handle_high_memory_usage(worker_id, metrics)

        except Exception as e:
            await self._handle_monitoring_error(worker_id, e)
```

## Worker Isolation and Security

### Process Isolation
- **Separate Process**: Each worker runs in its own process
- **Workspace Isolation**: Unique workspace per worker
- **Permission Boundaries**: Tool permissions enforced at process level
- **Memory Isolation**: Process memory not shared between workers

### Context Isolation
```python
class ContextIsolation:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)

    async def isolate_task_context(self, task_id: str, context: Dict[str, Any]):
        """Create isolated context for a task."""
        task_workspace = self.workspace_root / task_id
        task_workspace.mkdir(parents=True, exist_ok=True)

        # Save context
        context_file = task_workspace / "context.json"
        with open(context_file, 'w') as f:
            json.dump(context, f, indent=2)

        # Set up environment
        env = self._prepare_environment(context)

        return task_workspace, env

    def _prepare_environment(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Prepare environment variables for isolation."""
        env = os.environ.copy()

        # Add task-specific environment variables
        for key, value in context.get('environment', {}).items():
            env[key] = value

        # Remove sensitive information
        self._remove_sensitive_env(env)

        return env
```

### Security Boundaries
```python
class SecurityBoundary:
    def __init__(self, permissions: Dict[AgentRole, str]):
        self.permissions = permissions

    def get_allowed_tools(self, role: AgentRole) -> List[str]:
        """Get allowed tools for a role."""
        permission_level = self.permissions.get(role, "SAFE")

        # Define tool permissions per level
        tool_permissions = {
            "SAFE": ["read_files", "search", "analyze", "document"],
            "LIMITED": ["write_files", "run_tests", "install_dependencies"],
            "PRIVILEGED": ["deploy", "configure_infrastructure", "manage_secrets"],
            "DANGEROUS": ["delete_files", "execute_root_commands", "modify_production"]
        }

        return tool_permissions.get(permission_level, tool_permissions["SAFE"])

    def requires_approval(self, role: AgentRole, action: str) -> bool:
        """Check if an action requires human approval."""
        if role.permissions_level == "DANGEROUS":
            return True

        # Check specific actions that require approval
        dangerous_actions = [
            "delete_files",
            "execute_root_commands",
            "modify_production",
            "deploy_to_production",
            "make_payment",
            "modify_database_schema"
        ]

        return action in dangerous_actions
```

## Worker Communication and Coordination

### Orchestrator-Worker Communication
```python
class OrchestratorCommunication:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    async def send_task_to_worker(self, worker_id: str, task_spec: TaskSpecification):
        """Send task to worker via API."""
        payload = {
            "task_id": task_spec.task_id,
            "role": task_spec.role.value,
            "description": task_spec.description,
            "required_skills": task_spec.required_skills,
            "context": task_spec.context,
            "input_artifacts": task_spec.input_artifacts,
            "tool_permissions": task_spec.tool_permissions,
            "dependencies": task_spec.dependencies
        }

        response = await self.api_client.post(
            f"/api/workers/{worker_id}/tasks",
            json=payload
        )

        return response.json()

    async def get_worker_status(self, worker_id: str) -> WorkerStatus:
        """Get current status of a worker."""
        response = await self.api_client.get(f"/api/workers/{worker_id}/status")
        return WorkerStatus(**response.json())
```

### Worker-Worker Communication
```python
class WorkerCommunication:
    def __init__(self, message_bus: MessageBus):
        self.message_bus = message_bus

    async def broadcast_event(self, event: Event):
        """Broadcast event to all workers."""
        await self.message_bus.publish("worker_events", event)

    async def send_direct_message(self, target_worker_id: str, message: Message):
        """Send direct message to specific worker."""
        await self.message_bus.send(target_worker_id, message)
```

## Monitoring and Metrics

### Worker Metrics
```python
class WorkerMetrics:
    def __init__(self):
        self.start_time = time.time()
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.total_execution_time = 0.0
        self.cpu_usage_samples = []
        self.memory_usage_samples = []
        self.skill_usage = defaultdict(int)

    def record_task_completion(self, task_id: str, execution_time: float, success: bool):
        """Record task completion metrics."""
        self.tasks_completed += 1 if success else 0
        self.tasks_failed += 0 if success else 1
        self.total_execution_time += execution_time

    def record_resource_usage(self, cpu_percent: float, memory_percent: float):
        """Record resource usage metrics."""
        self.cpu_usage_samples.append(cpu_percent)
        self.memory_usage_samples.append(memory_usage)

    def record_skill_usage(self, skill_name: str):
        """Record skill usage."""
        self.skill_usage[skill_name] += 1
```

### Performance Indicators
- **Task Throughput**: Tasks completed per hour
- **Average Task Duration**: Mean time to complete tasks
- **Worker Utilization**: Percentage of worker time spent on tasks
- **Resource Efficiency**: CPU and memory usage per task
- **Task Success Rate**: Percentage of successfully completed tasks
- **Worker Response Time**: Time from task assignment to completion

## Worker Pool Configuration API

### Configuration Management
```python
class WorkerPoolConfig:
    def __init__(self, config_dict: Dict[str, Any]):
        self.config = config_dict

    @property
    def max_concurrent_workers(self) -> int:
        return self.config.get('worker_pool', {}).get('max_concurrent_workers', 2)

    @property
    def worker_template(self) -> Dict[str, Any]:
        return self.config.get('worker_pool', {}).get('worker_template', {})

    @property
    def agent_roles(self) -> Dict[str, Any]:
        return self.config.get('agent_roles', {})

    def update_config(self, new_config: Dict[str, Any]):
        """Update worker pool configuration."""
        self.config.update(new_config)
        # Apply changes to running workers
        asyncio.create_task(self._apply_config_changes())
```

### Configuration Endpoints
```python
@app.get("/api/worker-pool/config")
async def get_worker_pool_config():
    """Get current worker pool configuration."""
    return worker_pool.config

@app.post("/api/worker-pool/config")
async def update_worker_pool_config(new_config: Dict[str, Any]):
    """Update worker pool configuration."""
    await worker_pool.update_config(new_config)
    return {"status": "updated", "config": worker_pool.config}

@app.get("/api/worker-pool/status")
async def get_worker_pool_status():
    """Get worker pool status."""
    status = {
        "total_workers": len(worker_pool.workers),
        "available_workers": worker_pool.available_workers.qsize(),
        "busy_workers": len(worker_pool.busy_workers),
        "max_concurrent_workers": worker_pool.max_concurrent_workers,
        "utilization_rate": len(worker_pool.busy_workers) / worker_pool.max_concurrent_workers
    }
    return status
```

## Conclusion

The worker architecture in NexusForge provides a **flexible, scalable, and secure execution environment** for AI agent roles. Key characteristics include:

1. **Dynamic Role Assignment**: Workers load logical roles as needed
2. **Resource Efficiency**: Reusable workers with configurable pool size
3. **Security Isolation**: Process-level and context-level isolation
4. **Performance Monitoring**: Comprehensive metrics and monitoring
5. **Scalability**: Dynamic scaling based on workload
6. **Reliability**: Health checks and automatic recovery
7. **Extensibility**: Plugin architecture for new worker types

This architecture successfully implements the core principle from the NexusForge specification: **Workers are execution resources that dynamically load agent roles**, enabling a truly flexible and reusable AI agent orchestration platform.