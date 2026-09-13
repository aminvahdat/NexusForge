import axios from "axios";
import {
  Project, Task, HealthResponse,
  ProjectCreate, TaskCreate, TaskUpdate, ApiError,
  Execution, ExecutionEvent, ExecutionCreateResponse, ExecutionCompleteResponse,
  ExecutionStatusResponse, ExecutionListResponse,
  Worker, WorkerListResponse, WorkerDetailResponse,
  WebSocketMessage, ProjectMessage, WorkspaceFile
} from "../types";

// All requests go through nginx at the same origin — no host/port needed
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "/api",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: attach Bearer token from localStorage
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const apiError: ApiError = {
      detail: error.response?.data?.detail || error.message || "An unknown error occurred",
    };
    return Promise.reject(apiError);
  }
);

// === AUTH API ===
export const authApi = {
  login: async (credentials: { email: string; password: string }) => {
    const response = await apiClient.post<{ access_token: string; token_type: string }>("/auth/login", credentials);
    return response.data;
  },

  register: async (data: { email: string; password: string; username?: string }) => {
    const response = await apiClient.post<{ access_token: string; token_type: string }>("/auth/register", data);
    return response.data;
  },

  me: async () => {
    const response = await apiClient.get<{
      user: {
        id: string;
        email: string;
        username: string;
        is_active: boolean;
        is_superuser: boolean;
        email_verified?: boolean;
        has_configured_provider?: boolean;
      };
    }>("/auth/me");
    return response.data;
  },

  logout: async () => {
    const response = await apiClient.post("/auth/logout");
    return response.data;
  },
};

// === PROJECT API ===
export const projectApi = {
  getAll: async (status?: string): Promise<Project[]> => {
    const url = status ? `/projects?status=${encodeURIComponent(status)}` : "/projects";
    const response = await apiClient.get<Project[]>(url);
    return response.data;
  },

  getById: async (projectId: string): Promise<Project> => {
    const response = await apiClient.get<Project>(`/projects/${projectId}`);
    return response.data;
  },

  create: async (projectData: ProjectCreate): Promise<Project> => {
    const response = await apiClient.post<Project>("/projects", projectData);
    return response.data;
  },

  archive: async (projectId: string): Promise<Project> => {
    const response = await apiClient.post<Project>(`/projects/${projectId}/archive`);
    return response.data;
  },

  unarchive: async (projectId: string): Promise<Project> => {
    const response = await apiClient.post<Project>(`/projects/${projectId}/unarchive`);
    return response.data;
  },

  delete: async (projectId: string): Promise<{ message: string; id: string }> => {
    const response = await apiClient.delete<{ message: string; id: string }>(`/projects/${projectId}`);
    return response.data;
  },

  update: async (projectId: string, updateData: Partial<Project>): Promise<Project> => {
    const response = await apiClient.put<Project>(`/projects/${projectId}`, updateData);
    return response.data;
  },

  getAgentTraces: async (projectId: string): Promise<{ project_id: string; workspace: string; traces: any[]; count: number }> => {
    const response = await apiClient.get<{ project_id: string; workspace: string; traces: any[]; count: number }>(`/projects/${projectId}/agent-traces`);
    return response.data;
  },

  getMessages: async (projectId: string): Promise<{ project_id: string; messages: ProjectMessage[] }> => {
    const response = await apiClient.get<{ project_id: string; messages: ProjectMessage[] }>(`/projects/${projectId}/messages`);
    return response.data;
  },

  sendMessage: async (projectId: string, content: string): Promise<{ user_message: ProjectMessage; hermes_message: ProjectMessage; assistant_message?: ProjectMessage; trigger_build: boolean }> => {
    const response = await apiClient.post<{ user_message: ProjectMessage; hermes_message: ProjectMessage; assistant_message?: ProjectMessage; trigger_build: boolean }>(`/projects/${projectId}/messages`, { content });
    return response.data;
  },

  getModels: async (projectId: string): Promise<any> => {
    const response = await apiClient.get(`/projects/${projectId}/models`);
    return response.data;
  },

  getFiles: async (projectId: string): Promise<{ workspace: string; files: WorkspaceFile[] }> => {
    const response = await apiClient.get<{ workspace: string; files: WorkspaceFile[] }>(`/projects/${projectId}/files`);
    return response.data;
  },

  getFileContent: async (projectId: string, path: string): Promise<{ path: string; content: string; size: number }> => {
    const response = await apiClient.get<{ path: string; content: string; size: number }>(`/projects/${projectId}/files/content`, {
      params: { path }
    });
    return response.data;
  },

  runTerminal: async (projectId: string, command: string): Promise<{ command: string; stdout: string; stderr: string; exit_code: number; duration: number }> => {
    const response = await apiClient.post(`/projects/${projectId}/terminal/exec`, { command });
    return response.data;
  },

  run: async (projectId: string): Promise<any> => {
    const response = await apiClient.post(`/projects/${projectId}/run`);
    return response.data;
  },

  runProject: async (projectId: string): Promise<any> => {
    const response = await apiClient.post(`/projects/${projectId}/run`);
    return response.data;
  },
};

// === TASK API ===
export const taskApi = {
  getAll: async (): Promise<Task[]> => {
    const response = await apiClient.get<Task[]>("/tasks");
    return response.data;
  },

  getAllByProject: async (projectId: string): Promise<Task[]> => {
    const response = await apiClient.get<Task[]>(`/projects/${projectId}/tasks`);
    return response.data;
  },

  getById: async (taskId: string): Promise<Task> => {
    const response = await apiClient.get<Task>(`/tasks/${taskId}`);
    return response.data;
  },

  create: async (projectId: string, taskData: TaskCreate): Promise<Task> => {
    const response = await apiClient.post<Task>(`/projects/${projectId}/tasks`, taskData);
    return response.data;
  },

  update: async (taskId: string, taskData: TaskUpdate): Promise<Task> => {
    const response = await apiClient.put<Task>(`/tasks/${taskId}`, taskData);
    return response.data;
  },

  delete: async (taskId: string): Promise<{ message: string; id: string }> => {
    const response = await apiClient.delete<{ message: string; id: string }>(`/tasks/${taskId}`);
    return response.data;
  },

  run: async (taskId: string): Promise<any> => {
    const response = await apiClient.post(`/tasks/${taskId}/run`);
    return response.data;
  },
};

// === ARTIFACT API ===
export const artifactApi = {
  getByProject: async (projectId: string): Promise<any[]> => {
    const response = await apiClient.get(`/artifacts/project/${projectId}`);
    return response.data;
  },

  getContent: async (artifactId: string): Promise<{ id: string; name: string; type: string; path: string; content: string }> => {
    const response = await apiClient.get(`/artifacts/${artifactId}/content`);
    return response.data;
  },
};

// === HEALTH API ===
export const healthApi = {
  check: async (): Promise<HealthResponse> => {
    const response = await apiClient.get<HealthResponse>("/health");
    return response.data;
  },

  // Direct root endpoint — backend serves /health via router, but / is root
  checkHealthDirect: async (): Promise<HealthResponse> => {
    const response = await apiClient.get<HealthResponse>("/health/health");
    return response.data;
  },

  readiness: async (): Promise<HealthResponse> => {
    const response = await apiClient.get<HealthResponse>("/health");
    return response.data;
  },
};

// === EXECUTION API (Phase 5.4) ===
export const executionApi = {
  start: async (taskId: string): Promise<ExecutionCreateResponse> => {
    const response = await apiClient.post<ExecutionCreateResponse>(`/execution/start/${taskId}`);
    return response.data;
  },

  complete: async (
    executionId: string,
    result?: string,
    error?: string
  ): Promise<ExecutionCompleteResponse> => {
    const params = new URLSearchParams();
    if (result) params.append("result", result);
    if (error) params.append("error", error);
    const response = await apiClient.post<ExecutionCompleteResponse>(
      `/execution/${executionId}/complete?${params.toString()}`
    );
    return response.data;
  },

  cancel: async (executionId: string): Promise<{ execution_id: string; status: string; message: string }> => {
    const response = await apiClient.post(`/execution/${executionId}/cancel`);
    return response.data;
  },

  status: async (executionId: string): Promise<ExecutionStatusResponse> => {
    const response = await apiClient.get<ExecutionStatusResponse>(`/execution/status/${executionId}`);
    return response.data;
  },

  list: async (): Promise<ExecutionListResponse> => {
    const response = await apiClient.get<ExecutionListResponse>("/execution/list");
    return response.data;
  },
};

// === WORKER API (Phase 5.4) ===
export const workerApi = {
  getAll: async (): Promise<WorkerListResponse> => {
    const response = await apiClient.get<WorkerListResponse>("/workers");
    return response.data;
  },

  getById: async (workerId: string): Promise<WorkerDetailResponse> => {
    const response = await apiClient.get<WorkerDetailResponse>(`/workers/${workerId}`);
    return response.data;
  },

  pause: async (workerId: string) => {
    const response = await apiClient.post(`/workers/pause/${workerId}`);
    return response.data;
  },

  resume: async (workerId: string) => {
    const response = await apiClient.post(`/workers/resume/${workerId}`);
    return response.data;
  },

  retire: async (workerId: string) => {
    const response = await apiClient.post(`/workers/retire/${workerId}`);
    return response.data;
  },
};

// === SETTINGS API ===
export const settingsApi = {
  getKeys: async () => {
    const res = await apiClient.get("/settings/keys");
    return res.data;
  },
  createKey: async (data: any) => {
    const res = await apiClient.post("/settings/keys", data);
    return res.data;
  },
  deleteKey: async (keyId: string) => {
    const res = await apiClient.delete(`/settings/keys/${keyId}`);
    return res.data;
  },
  testKey: async (data: { provider: string; api_key: string; base_url?: string }) => {
    const res = await apiClient.post("/settings/test-key", data);
    return res.data;
  },
  fetchModels: async (data: { provider: string; api_key?: string; base_url?: string }) => {
    const res = await apiClient.post("/settings/fetch-models", data);
    return res.data;
  },
  recommendRoles: async (data: { provider: string; api_key?: string; base_url?: string }) => {
    const res = await apiClient.post("/settings/recommend-roles", data);
    return res.data;
  },
  applyRecommendations: async (data: { provider: string; recommendations: any[] }) => {
    const res = await apiClient.post("/settings/apply-recommendations", data);
    return res.data;
  },
  getSystem: async () => {
    const res = await apiClient.get("/settings/system");
    return res.data;
  },
  updateSystem: async (data: any) => {
    const res = await apiClient.post("/settings/system", data);
    return res.data;
  },
};

// === AGENT CONFIGURATION API ===
export const agentApi = {
  getAll: async () => {
    const res = await apiClient.get("/agents");
    return res.data;
  },
  getById: async (agentId: string) => {
    const res = await apiClient.get(`/agents/${agentId}`);
    return res.data;
  },
  create: async (data: any) => {
    const res = await apiClient.post("/agents", data);
    return res.data;
  },
  update: async (agentId: string, data: any) => {
    const res = await apiClient.put(`/agents/${agentId}`, data);
    return res.data;
  },
  delete: async (agentId: string) => {
    const res = await apiClient.delete(`/agents/${agentId}`);
    return res.data;
  },
  reset: async () => {
    const res = await apiClient.post("/agents/reset");
    return res.data;
  },
};

export default apiClient;
export { apiClient as api };
