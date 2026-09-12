// Core types and enums
export { AgentRole, Priority, TaskStatus, ExecutionStatus } from "./enums";

// Health check types
export interface HealthCheck {
  status: string;
  database?: boolean;
  redis?: boolean;
}

export interface HealthResponse {
  status: string;
  version?: string;
  checks?: HealthCheck;
}

// Execution event types
export interface ExecutionEvent {
  id: string;
  event_type: string;
  execution_status?: string;
  timestamp: string;
  worker_id?: string;
  execution_id?: string;
  message?: string;
}

// WebSocket message types
export interface WebSocketMessage {
  type: string;
  data?: ExecutionEvent;
  message?: string;
}

// Approval types
export interface ApprovalRequest {
  id: string;
  execution_id: string;
  agent_name: string;
  agent_role: AgentRole;
  action_type: string;
  action_description: string;
  reasoning: string;
  potential_impact: string;
  requires_human_approval: boolean;
  status: string;
  requested_by: string;
  requested_at: string;
  expires_at: string | null;
  approved_by: string | null;
  approved_at: string | null;
  rejected_by: string | null;
  rejected_at: string | null;
  rejection_reason: string | null;
  cancelled_by: string | null;
  cancelled_at: string | null;
  cancellation_reason: string | null;
  updated_at: string;
  is_expired: boolean;
  is_pending: boolean;
}

export interface ApprovalCreate {
  execution_id?: string;
  agent_name?: string;
  agent_role?: AgentRole;
  action_type: string;
  action_description: string;
  reasoning: string;
  potential_impact: string;
  expires_at?: string;
}

export interface ApprovalUpdate {
  action_type?: string;
  action_description?: string;
  reasoning?: string;
  potential_impact?: string;
  expires_at?: string;
}

export interface ApprovalListResponse {
  approvals: ApprovalRequest[];
  count: number;
}

// Artifact types
export interface Artifact {
  id: string;
  project_id: string;
  task_id: string | null;
  execution_id: string | null;
  name: string;
  type: string;
  version: number;
  description: string | null;
  path: string | null;
  size: number | null;
  mime_type: string | null;
  checksum: string | null;
  author_id: string | null;
  created_at: string;
  extra_data: Record<string, any> | null;
  is_public: boolean;
}

export interface ArtifactCreate {
  project_id: string;
  task_id?: string | null;
  execution_id?: string | null;
  name: string;
  type: string;
  description?: string | null;
  path?: string | null;
  size?: number | null;
  mime_type?: string | null;
  checksum?: string | null;
  is_public?: boolean;
}

export interface ArtifactUpdate {
  name?: string | null;
  description?: string | null;
  path?: string | null;
  size?: number | null;
  mime_type?: string | null;
  checksum?: string | null;
  is_public?: boolean | null;
}

export interface ArtifactResponse {
  id: string;
  project_id: string;
  task_id: string | null;
  execution_id: string | null;
  name: string;
  type: string;
  version: number;
  description: string | null;
  path: string | null;
  size: number | null;
  mime_type: string | null;
  checksum: string | null;
  author_id: string | null;
  created_at: string;
  extra_data: Record<string, any> | null;
  is_public: boolean;
}

export interface ArtifactListResponse {
  artifacts: Artifact[];
  count: number;
}

// Task types
export interface Task {
  id: string;
  project_id: string;
  title: string;
  description: string;
  role: AgentRole;
  required_skills: string[];
  dependencies: string[];
  input_artifacts: string[];
  output_artifacts: string[];
  acceptance_criteria: string[];
  priority: Priority;
  status: TaskStatus;
  retry_count: number;
  max_retries: number;
  due_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskCreate {
  project_id: string;
  title: string;
  description: string;
  role: AgentRole;
  required_skills: string[];
  dependencies: string[];
  input_artifacts: string[];
  output_artifacts: string[];
  acceptance_criteria: string[];
  priority: Priority;
  status: TaskStatus;
  retry_count: number;
  max_retries: number;
  due_date: string | null;
}

export interface TaskUpdate {
  title?: string;
  description?: string;
  role?: AgentRole;
  required_skills?: string[];
  dependencies?: string[];
  input_artifacts?: string[];
  output_artifacts?: string[];
  acceptance_criteria?: string[];
  priority?: Priority;
  status?: TaskStatus;
  retry_count?: number;
  max_retries?: number;
  due_date?: string | null;
}

export interface TaskListResponse {
  tasks: Task[];
  count: number;
}

// Project types
export interface Project {
  id: string;
  name: string;
  description: string;
  status?: string;
  owner_id: string;
  ai_provider: string | null;
  ai_model: string | null;
  preferred_language: string;
  timezone: string;
  telegram_notifications_enabled: boolean;
  telegram_chat_id: string | null;
  workspace_path?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  description: string;
  owner_id?: string;
  status?: string;
  ai_provider?: string | null;
  ai_model?: string | null;
  preferred_language?: string;
  timezone?: string;
  telegram_notifications_enabled?: boolean;
  telegram_chat_id?: string | null;
  workspace_path?: string | null;
}

export interface AgentTrace {
  role: string;
  agent_name: string;
  badge: string;
  status: string;
  duration?: string;
  model?: string;
  thoughts: string[];
  output_title: string;
  output_type: string;
  output_content: string;
  file_path?: string;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  owner_id?: string;
  ai_provider?: string | null;
  ai_model?: string | null;
  preferred_language?: string;
  timezone?: string;
  telegram_notifications_enabled?: boolean;
  telegram_chat_id?: string | null;
}

export interface ProjectListResponse {
  projects: Project[];
  count: number;
}

// Worker types
export interface Worker {
  id: string;
  worker_id: string;
  hostname: string;
  status: string;
  current_task_id: string | null;
  last_heartbeat: string;
  started_at: string;
  meta_info: Record<string, any> | null;
  execution_events: ExecutionEvent[];
}

export interface WorkerState {
  worker_id: string;
  hostname: string;
  status: string;
  current_task_id: string | null;
  last_heartbeat: string;
  started_at: string;
  meta_info: Record<string, any> | null;
}

export interface WorkerControl {
  id: string;
  worker_id: string;
  action: string;
  requested_by: string;
  requested_at: string;
  reason: string;
  status: string;
  executed_at: string | null;
}

export interface WorkerListResponse {
  workers: Worker[];
  count: number;
}

export interface ProjectMessage {
  id: string;
  project_id: string;
  sender: 'user' | 'hermes' | 'system';
  content: string;
  metadata?: {
    type?: string;
    quick_chips?: string[];
    models?: Record<string, any>;
    trigger_build?: boolean;
    [key: string]: any;
  };
  created_at: string;
}

export interface WorkspaceFile {
  path: string;
  name: string;
  size: number;
  modified: string;
  ext: string;
}