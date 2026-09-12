import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Task, TaskCreate, TaskStatus, AgentRole, Priority } from "../types";
import { taskApi } from "../services/api";
import Loading from "../components/Loading";

const TaskListPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const [taskFormData, setTaskFormData] = useState<TaskCreate>({
    project_id: projectId,
    title: "",
    description: "",
    role: AgentRole.PROJECT_PLANNER,
    required_skills: [],
    dependencies: [],
    input_artifacts: [],
    output_artifacts: [],
    acceptance_criteria: [],
    priority: Priority.MEDIUM,
    status: TaskStatus.QUEUED,
    retry_count: 0,
    max_retries: 3,
    due_date: null,
  });

  const fetchTasks = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await taskApi.getAllByProject(projectId);
      setTasks(data);
    } catch (err: any) {
      setError(err.detail || "Failed to load tasks");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (projectId) {
      fetchTasks();
    }
  }, [projectId]);

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setCreateLoading(true);
      setCreateError(null);
      const newTask = await taskApi.create(projectId, taskFormData);
      setTasks((prev) => [...prev, newTask]);
      setShowCreateModal(false);
      // Reset form
      setTaskFormData({
        project_id: projectId,
        title: "",
        description: "",
        role: AgentRole.PROJECT_PLANNER,
        required_skills: [],
        dependencies: [],
        input_artifacts: [],
        output_artifacts: [],
        acceptance_criteria: [],
        priority: Priority.MEDIUM,
        status: TaskStatus.QUEUED,
        retry_count: 0,
        max_retries: 3,
        due_date: null,
      });
    } catch (err: any) {
      setCreateError(err.detail || "Failed to create task");
    } finally {
      setCreateLoading(false);
    }
  };

  const handleTaskStatusChange = async (taskId: string, newStatus: string) => {
    try {
      const updated = await taskApi.update(taskId, { status: newStatus });
      setTasks((prev) => prev.map((t) => (t.id === taskId ? updated : t)));
    } catch (err: any) {
      setError(err.detail || "Failed to update task status");
    }
  };

  const handleInputChange = (field: keyof TaskCreate, value: any) => {
    setTaskFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleStringListChange = (field: keyof TaskCreate, value: string) => {
    const items = value
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
    handleInputChange(field, items.length > 0 ? items : []);
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "-";
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const priorityIcons: Record<string, string> = {
    low: "●",
    medium: "◐",
    high: "▲",
    critical: "■",
  };

  const statusColors: Record<string, string> = {
    queued: "bg-slate-100 text-slate-700 border-slate-300",
    planning: "bg-blue-100 text-blue-700 border-blue-300",
    blocked: "bg-red-100 text-red-700 border-red-300",
    ready: "bg-yellow-100 text-yellow-700 border-yellow-300",
    running: "bg-indigo-100 text-indigo-700 border-indigo-300",
    waiting: "bg-purple-100 text-purple-700 border-purple-300",
    reviewing: "bg-teal-100 text-teal-700 border-teal-300",
    needs_revision: "bg-orange-100 text-orange-700 border-orange-300",
    completed: "bg-green-100 text-green-700 border-green-300",
    failed: "bg-red-100 text-red-700 border-red-300",
    cancelled: "bg-gray-100 text-gray-700 border-gray-300",
  };

  const agentRoles = Object.entries(AgentRole).map(([key, value]) => ({
    label: key.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()),
    value: value,
  }));

  if (loading) {
    return <Loading message="Loading tasks..." />;
  }

  return (
    <div className="page page--tasks">
      <header className="page__header">
        <button
          className="btn btn-outline"
          onClick={() => navigate("/projects")}
          aria-label="Back to projects"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="5" y1="12" x2="19" y2="12"></line>
            <polyline points="12 5 5 12 12 19"></polyline>
          </svg>
        </button>
        <div className="page__title-section">
          <h1 className="page__title">Tasks</h1>
          <p className="page__subtitle">
            Manage tasks for this project
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
          <svg className="btn__icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          Add Task
        </button>
      </header>

      {error && (
        <div className="alert alert-error" role="alert">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
          <span>{error}</span>
        </div>
      )}

      {tasks.length === 0 && !error && (
        <div className="empty-state">
          <svg className="empty-state__icon" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <line x1="8" y1="6" x2="21" y2="6"></line>
            <line x1="8" y1="12" x2="21" y2="12"></line>
            <line x1="8" y1="18" x2="13" y2="18"></line>
            <line x1="3" y1="6" x2="3.01" y2="6"></line>
            <line x1="3" y1="12" x2="3.01" y2="12"></line>
            <line x1="3" y1="18" x2="3.01" y2="18"></line>
          </svg>
          <h3 className="empty-state__title">No Tasks Yet</h3>
          <p className="empty-state__description">
            Create a task to get started with this project.
          </p>
          <button className="btn btn-primary empty-state__action" onClick={() => setShowCreateModal(true)}>
            Create Task
          </button>
        </div>
      )}

      {tasks.length > 0 && (
        <div className="page__task-list" role="list">
          {tasks.map((task) => (
            <article key={task.id} className="page__task-item" role="listitem">
              <div className="page__task-main">
                <h4 className="page__task-title">{task.title}</h4>
                <div className="page__task-meta">
                  <span className="page__task-priority">
                    <span className="priority-badge" role="img" aria-label={`${task.priority} priority`}>
                      {priorityIcons[task.priority] || "●"} {task.priority}
                    </span>
                  </span>
                  <span className="page__task-status">
                    <span className={`status-badge ${statusColors[task.status] || "bg-gray-100 text-gray-700 border-gray-300"}`}>
                      {task.status.replace(/_/g, " ")}
                    </span>
                  </span>
                  <span className="page__task-role">
                    <span className="role-badge">{task.role.replace(/_/g, " ")}</span>
                  </span>
                </div>
              </div>

              <div className="page__task-actions">
                {task.status !== "completed" && task.status !== "failed" && task.status !== "cancelled" && (
                  <select
                    className="input input--small"
                    value={task.status}
                    onChange={(e) => handleTaskStatusChange(task.id, e.target.value)}
                    aria-label={`Change status for ${task.title}`}
                  >
                    <option value="queued">Queued</option>
                    <option value="planning">Planning</option>
                    <option value="ready">Ready</option>
                    <option value="running">Running</option>
                    <option value="waiting">Waiting</option>
                    <option value="completed">Completed</option>
                    <option value="failed">Failed</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                )}
              </div>

              <footer className="page__task-footer">
                <time className="page__task-time" dateTime={task.created_at}>
                  {formatDate(task.created_at)}
                </time>
                {task.retry_count > 0 && (
                  <span className="page__task-retries" title="Retry count">
                    ↻ {task.retry_count}
                  </span>
                )}
                {task.due_date && (
                  <span className="page__task-due" title="Due date">
                    Due {formatDate(task.due_date)}
                  </span>
                )}
              </footer>
            </article>
          ))}
        </div>
      )}

      {/* Create Task Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)} role="dialog" aria-modal="true" aria-labelledby="create-task-title">
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <header className="modal__header">
              <h2 id="create-task-title" className="modal__title">Create New Task</h2>
              <button className="modal__close" onClick={() => setShowCreateModal(false)} aria-label="Close">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </header>
            <form onSubmit={handleCreateTask} className="modal__body" noValidate>
              {createError && (
                <div className="alert alert-error" role="alert">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                  </svg>
                  <span>{createError}</span>
                </div>
              )}

              <div className="form-group">
                <label htmlFor="task-title" className="label">Task Title *</label>
                <input
                  type="text"
                  id="task-title"
                  className="input"
                  value={taskFormData.title}
                  onChange={(e) => handleInputChange("title", e.target.value)}
                  required
                  placeholder="What needs to be done?"
                  maxLength={500}
                  autoFocus
                />
              </div>

              <div className="form-group">
                <label htmlFor="task-description" className="label">Description *</label>
                <textarea
                  id="task-description"
                  className="input textarea"
                  value={taskFormData.description}
                  onChange={(e) => handleInputChange("description", e.target.value)}
                  required
                  placeholder="Detailed description of the task..."
                  rows={4}
                />
              </div>

              <div className="form-group">
                <label htmlFor="task-role" className="label">Agent Role</label>
                <select
                  id="task-role"
                  className="input select"
                  value={taskFormData.role}
                  onChange={(e) => handleInputChange("role", e.target.value)}
                >
                  {agentRoles.map((role) => (
                    <option key={role.value} value={role.value}>
                      {role.label}
                    </option>
                  ))}
                </select>
                <p className="form-helper-text">
                  Agent roles are logical profiles — selecting a role assigns a specific
                  task type, not a permanent worker. The worker pool manages execution.
                </p>
              </div>

              <div className="form-group">
                <label htmlFor="task-priority" className="label">Priority</label>
                <select
                  id="task-priority"
                  className="input select"
                  value={taskFormData.priority}
                  onChange={(e) => handleInputChange("priority", e.target.value)}
                >
                  <option value={Priority.LOW}>Low</option>
                  <option value={Priority.MEDIUM}>Medium</option>
                  <option value={Priority.HIGH}>High</option>
                  <option value={Priority.CRITICAL}>Critical</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="task-required-skills" className="label">Required Skills</label>
                <input
                  type="text"
                  id="task-required-skills"
                  className="input"
                  value={(taskFormData.required_skills || []).join(", ")}
                  onChange={(e) => handleStringListChange("required_skills", e.target.value)}
                  placeholder="e.g., react, typescript, postgresql"
                />
                <p className="form-helper-text">Comma-separated list of required skills</p>
              </div>

              <div className="form-group">
                <label htmlFor="task-due-date" className="label">Due Date</label>
                <input
                  type="date"
                  id="task-due-date"
                  className="input"
                  value={taskFormData.due_date ? new Date(taskFormData.due_date).toISOString().split("T")[0] : ""}
                  onChange={(e) => handleInputChange("due_date", e.target.value || null)}
                />
              </div>

              <div className="form-group">
                <label htmlFor="task-max-retries" className="label">Max Retries</label>
                <input
                  type="number"
                  id="task-max-retries"
                  className="input"
                  min="0"
                  max="10"
                  value={taskFormData.max_retries}
                  onChange={(e) => handleInputChange("max_retries", parseInt(e.target.value, 10))}
                />
              </div>

              <div className="form-group">
                <label htmlFor="task-acceptance-criteria" className="label">Acceptance Criteria</label>
                <textarea
                  id="task-acceptance-criteria"
                  className="input textarea"
                  value={(taskFormData.acceptance_criteria || []).join("\n")}
                  onChange={(e) => handleStringListChange("acceptance_criteria", e.target.value)}
                  placeholder="One criterion per line"
                  rows={3}
                />
              </div>

              <footer className="modal__footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateModal(false)} disabled={createLoading}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={createLoading || !taskFormData.title.trim() || !taskFormData.description.trim()}>
                  {createLoading ? (
                    <>
                      <span className="loading-spinner" style={{ width: "16px", height: "16px" }}></span>
                      Creating...
                    </>
                  ) : (
                    "Create Task"
                  )}
                </button>
              </footer>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskListPage;