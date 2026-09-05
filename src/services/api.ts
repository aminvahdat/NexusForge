import axios from "axios";
import { Project, Task, HealthResponse, ProjectCreate, TaskCreate, TaskUpdate, ApiError } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: `${API_BASE}/api`,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Auth tokens would be injected here when Phase 3 auth is implemented
    // For now, pass through without auth
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

// === PROJECT API ===
export const projectApi = {
  getAll: async (): Promise<Project[]> => {
    const response = await apiClient.get<Project[]>("/projects");
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
};

// === TASK API ===
export const taskApi = {
  getAllByProject: async (projectId: string, status?: string): Promise<Task[]> => {
    const params: Record<string, any> = {};
    if (status) params.status = status;
    const response = await apiClient.get<Task[]>(`/projects/${projectId}/tasks`, { params });
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
};

// === HEALTH API ===
export const healthApi = {
  check: async (): Promise<HealthResponse> => {
    const response = await apiClient.get<HealthResponse>("/health");
    return response.data;
  },

  readiness: async (): Promise<HealthResponse> => {
    const response = await apiClient.get<HealthResponse>("/health/readiness");
    return response.data;
  },
};

export default apiClient;