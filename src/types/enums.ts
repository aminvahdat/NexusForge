export enum AgentRole {
  CHIEF_ORCHESTRATOR = "chief_orchestrator",
  PROJECT_PLANNER = "project_planner",
  ARCHITECT = "architect",
  DEVELOPER = "developer",
  TESTER = "tester",
  REVIEWER = "reviewer",
  DEPLOYER = "deployer",
}

export enum Priority {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
  CRITICAL = "critical",
}

export enum TaskStatus {
  QUEUED = "queued",
  PLANNING = "planning",
  BLOCKED = "blocked",
  READY = "ready",
  RUNNING = "running",
  WAITING = "waiting",
  REVIEWING = "reviewing",
  NEEDS_REVISION = "needs_revision",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled",
}

export enum ExecutionStatus {
  STARTED = "started",
  RUNNING = "running",
  COMPLETED = "completed",
  FAILED = "failed",
  PAUSED = "paused",
  RESUMED = "resumed",
  RETIRED = "retired",
}

export enum WorkerStatus {
  IDLE = "idle",
  BUSY = "busy",
  OFFLINE = "offline",
  RETIRED = "retired",
}
