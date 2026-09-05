// TypeScript types matching the NexusForge backend API schemas

export interface Project {
  id: string;
  name: string;
  description: string | null;
  owner_id: string | null;
  ai_provider: string | null;
  ai_model: string | null;
  preferred_language: string | null;
  timezone: string | null;
  telegram_notifications_enabled: boolean | null;
  telegram_chat_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  project_id: string | null;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  role: string;
  required_skills: string[] | null;
  dependencies: string[] | null;
  input_artifacts: string[] | null;
  output_artifacts: string[] | null;
  assigned_worker_id: string | null;
  acceptance_criteria: string | null;
  retry_count: number | null;
  max_retries: number | null;
  due_date: string | null;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
  result: string | null;
  error: string | null;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  database: string;
  redis: string;
}

export interface HealthLiveness {
  status: string;
}

export interface HealthReadiness {
  status: string;
}

export interface ProjectCreate {
  name: string;
  description?: string | null;
  owner_id?: string | null;
  ai_provider?: string | null;
  ai_model?: string | null;
  preferred_language?: string | null;
  timezone?: string | null;
  telegram_notifications_enabled?: boolean | null;
  telegram_chat_id?: string | null;
}

export interface TaskCreate {
  task_id: string;
  project_id: string | null;
  title: string;
  description?: string | null;
  role?: string;
  required_skills?: string[] | null;
  dependencies?: string[] | null;
  input_artifacts?: string[] | null;
  output_artifacts?: string[] | null;
  assigned_worker?: string | null;
  acceptance_criteria?: string | null;
  retry_count?: number | null;
  max_retries?: number | null;
  due_date?: string | null;
}

export interface TaskUpdate {
  title?: string | null;
  description?: string | null;
  role?: string | null;
  priority?: string | null;
  status?: string | null;
  dependencies?: string[] | null;
  input_artifacts?: string[] | null;
  output_artifacts?: string[] | null;
  acceptance_criteria?: string | null;
  retry_count?: number | null;
  max_retries?: number | null;
  due_date?: string | null;
}

export interface ApiError {
  detail: string;
}