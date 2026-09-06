// Phase 5.3 — Existing types

export interface Project {
  id: string;
  name: string;
  description: string | null;
  owner_id: string;
  ai_provider: string | null;
  ai_model: string | null;
  preferred_language: string;
  timezone: string;
  telegram_notifications_enabled: boolean;
  telegram_chat_id: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  task_id: string | null;
  project_id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  role: string;
  required_skills: string[] | null;
  dependencies: string[] | null;
  input_artifacts: string[] | null;
  output_artifacts: string[] | null;
  acceptance_criteria: string[] | null;
  assigned_worker: string | null;
  retry_count: number;
  max_retries: number;
  due_date: string | null;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
  result: string | null;
  error: string | null;
  metadata: Record<string, any>;
  estimated_tokens: number | null;
  assignment_id: string | null;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  checks?: {
    database: boolean;
    redis: boolean;
  };
}

export interface HealthLiveness {
  status: string;
}

export interface HealthReadiness {
  status: string;
}

export interface ProjectCreate {
  name: string;
  description: string;
  owner_id: string;
  ai_provider?: string | null;
  ai_model?: string | null;
  preferred_language?: string;
  timezone?: string;
  telegram_notifications_enabled?: boolean;
  telegram_chat_id?: string | null;
}

export interface TaskCreate {
  task_id?: string | null;
  project_id: string;
  title: string;
  description: string;
  role: string;
  required_skills?: string[] | null;
  dependencies?: string[] | null;
  input_artifacts?: string[] | null;
  output_artifacts?: string[] | null;
  acceptance_criteria?: string[] | null;
  priority?: string;
  status?: string;
  retry_count?: number;
  max_retries?: number;
  due_date?: string | null;
}

export interface TaskUpdate {
  title?: string | null;
  description?: string | null;
  role?: string | null;
  required_skills?: string[] | null;
  dependencies?: string[] | null;
  input_artifacts?: string[] | null;
  output_artifacts?: string[] | null;
  acceptance_criteria?: string[] | null;
  priority?: string | null;
  status?: string | null;
  assigned_worker?: string | null;
  retry_count?: number | null;
  max_retries?: number | null;
  due_date?: string | null;
}

export interface ApiError {
  detail: string;
}

// Agent Role enum values from backend
export const AgentRole = {
  CHIEF_ORCHESTRATOR: "chief_orchestrator",
  PROJECT_PLANNER: "project_planner",
  SOFTWARE_ARCHITECT: "software_architect",
  RESEARCH_AGENT: "research_agent",
  UI_UX_AGENT: "ui_ux_agent",
  FRONTEND_AGENT: "frontend_agent",
  BACKEND_AGENT: "backend_agent",
  MOBILE_AGENT: "mobile_agent",
  DATABASE_AGENT: "database_agent",
  SECURITY_AGENT: "security_agent",
  QA_AGENT: "qa_agent",
  DEVOPS_AGENT: "devops_agent"
} as const;

// Task Status enum values from backend
export const TaskStatus = {
  QUEUED: "queued",
  PLANNING: "planning",
  BLOCKED: "blocked",
  READY: "ready",
  RUNNING: "running",
  WAITING: "waiting",
  REVIEWING: "reviewing",
  NEEDS_REVISION: "needs_revision",
  COMPLETED: "completed",
  FAILED: "failed",
  CANCELLED: "cancelled"
} as const;

// Priority enum values from backend
export const Priority = {
  LOW: "low",
  MEDIUM: "medium",
  HIGH: "high",
  CRITICAL: "critical"
} as const;

// Worker Status enum values from backend
export const WorkerStatus = {
  IDLE: "idle",
  BUSY: "busy",
  ERROR: "error",
  OFFLINE: "offline"
} as const;

// Phase 5.4 — Execution types
export * from "./execution";