// Execution-related types for Phase 5.4 (Live Execution Monitoring)

export interface Execution {
  execution_id: string;
  task_id: string;
  worker_id: string | null;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  result: string | null;
  error: string | null;
  events: number;
}

export interface ExecutionEvent {
  event_type: string;
  message: string;
  execution_id: string;
  worker_id: string | null;
  task_id: string | null;
  timestamp: string;
  metadata: Record<string, any>;
}

export interface ExecutionCreateResponse {
  execution_id: string;
  status: string;
  event: ExecutionEvent;
}

export interface ExecutionCompleteResponse {
  execution_id: string;
  status: string;
  event: ExecutionEvent;
}

export interface ExecutionStatusResponse {
  execution_id: string;
  status: string;
  event: ExecutionEvent;
}

export interface ExecutionListResponse {
  active_executions: Record<string, {
    status: string;
    task_id: string;
    worker_id: string | null;
    events: number;
  }>;
  count: number;
}

export interface Worker {
  id: string;
  name: string;
  status: string;
  current_task: string | null;
  last_heartbeat: string | null;
  hostname: string;
  skills: string[];
  created_at: string;
}

export interface WorkerListResponse {
  workers: Worker[];
  count: number;
}

export interface WorkerDetailResponse {
  worker: Worker;
  current_execution: Execution | null;
  recent_events: ExecutionEvent[];
}

// WebSocket message types
export interface WebSocketMessage {
  type: "state_sync" | "execution_event" | "pong";
  executions?: Record<string, any>;
  event?: ExecutionEvent;
  count?: number;
}