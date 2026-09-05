import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Task, Project } from "../types";
import { taskApi, projectApi } from "../services/api";
import Loading from "../components/Loading";
import "./TaskDetail.css";

const TaskDetail: React.FC = () => {
  const { projectId, taskId } = useParams<{ projectId: string; taskId: string }>();
  const navigate = useNavigate();
  const [task, setTask] = useState<Task | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const [taskData, projectData] = await Promise.all([
          taskApi.getById(taskId),
          projectApi.getById(projectId),
        ]);
        setTask(taskData);
        setProject(projectData);
      } catch (err: any) {
        setError(err.detail || "Failed to load task data");
      } finally {
        setLoading(false);
      }
    };

    if (taskId && projectId) {
      fetchData();
    }
  }, [taskId, projectId]);

  const handleStatusChange = async (newStatus: string) => {
    try {
      const updated = await taskApi.update(taskId, { status: newStatus });
      setTask(updated);
    } catch (err: any) {
      setError(err.detail || "Failed to update task status");
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "-";
    return new Date(dateString).toLocaleString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const statusColors: Record<string, string> = {
    queued: "status-queued",
    planning: "status-planning",
    blocked: "status-blocked",
    ready: "status-ready",
    running: "status-running",
    waiting: "status-waiting",
    reviewing: "status-reviewing",
    needs_revision: "status-needs-revision",
    completed: "status-completed",
    failed: "status-failed",
    cancelled: "status-cancelled",
  };

  const getRoleLabel = (role: string) => {
    return role.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
  };

  if (loading) {
    return <Loading message="Loading task..." />;
  }

  if (error) {
    return (
      <div className="task-detail">
        <div className="alert alert-error" role="alert">
          <span>{error}</span>
          <button className="btn btn-outline btn-sm" onClick={() => navigate(-1)}>
            Go Back
          </button>
        </div>
      </div>
    );
  }

  if (!task || !project) {
    return (
      <div className="task-detail">
        <div className="alert alert-error" role="alert">
          Task or project not found.
        </div>
      </div>
    );
  }

  const canTransitionTo = (newStatus: string) => {
    const terminal = ["completed", "failed", "cancelled"];
    if (terminal.includes(task.status)) return false;
    return newStatus !== task.status;
  };

  const possibleTransitions = ["queued", "planning", "ready", "running", "waiting", "reviewing", "completed", "failed", "cancelled"].filter(status => 
    canTransitionTo(status) && status !== "queued"
  );

  return (
    <div className="task-detail">
      <header className="task-detail__header">
        <div className="task-detail__breadcrumb">
          <button className="btn btn-outline btn-sm" onClick={() => navigate("/projects")}>
            ← Projects
          </button>
          <span onClick={() => navigate(`/projects/${project.id}`)} className="task-detail__breadcrumb-item" style={{ cursor: "pointer", color: "var(--color-primary)" }}>
            {project.name}
          </span>
          <span className="task-detail__breadcrumb-separator">/</span>
          <span className="task-detail__breadcrumb-current">Task Detail</span>
        </div>
        <div className="task-detail__header-right">
          <span className={`status-badge ${statusColors[task.status] || "status-queued"}`}>
            {task.status.replace(/_/g, " ")}
          </span>
        </div>
      </header>

      <section className="task-detail__section">
        <h2 className="task-detail__section-title">Task Overview</h2>
        <div className="task-detail__grid">
          <div className="task-detail__field">
            <label className="task-detail__field-label">Task ID</label>
            <p className="task-detail__field-value mono">{task.id}</p>
          </div>
          <div className="task-detail__field">
            <label className="task-detail__field-label">Title</label>
            <h3 className="task-detail__field-value task-detail__field-value--title">{task.title}</h3>
          </div>
          <div className="task-detail__field">
            <label className="task-detail__field-label">Role</label>
            <p className="task-detail__field-value">
              <span className="role-badge">{getRoleLabel(task.role)}</span>
            </p>
          </div>
          <div className="task-detail__field">
            <label className="task-detail__field-label">Priority</label>
            <p className="task-detail__field-value">
              <span className="priority-badge">{task.priority}</span>
            </p>
          </div>
          <div className="task-detail__field">
            <label className="task-detail__field-label">Assigned Worker</label>
            <p className="task-detail__field-value mono">
              {task.assigned_worker || "Not assigned"}
            </p>
          </div>
        </div>
      </section>

      <section className="task-detail__section">
        <h2 className="task-detail__section-title">Description</h2>
        <div className="task-detail__content">
          <p className="task-detail__description">{task.description || "No description provided"}</p>
        </div>
      </section>

      <section className="task-detail__section">
        <h2 className="task-detail__section-title">Timing</h2>
        <div className="task-detail__grid">
          <div className="task-detail__field">
            <label className="task-detail__field-label">Created</label>
            <p className="task-detail__field-value mono">{formatDate(task.created_at)}</p>
          </div>
          <div className="task-detail__field">
            <label className="task-detail__field-label">Updated</label>
            <p className="task-detail__field-value mono">{formatDate(task.updated_at)}</p>
          </div>
          <div className="task-detail__field">
            <label className="task-detail__field-label">Started</label>
            <p className="task-detail__field-value mono">{formatDate(task.started_at)}</p>
          </div>
          <div className="task-detail__field">
            <label className="task-detail__field-label">Completed</label>
            <p className="task-detail__field-value mono">{formatDate(task.completed_at)}</p>
          </div>
          {task.due_date && (
            <div className="task-detail__field">
              <label className="task-detail__field-label">Due Date</label>
              <p className="task-detail__field-value mono">{formatDate(task.due_date)}</p>
            </div>
          )}
        </div>
      </section>

      <section className="task-detail__section">
        <h2 className="task-detail__section-title">Retry Information</h2>
        <div className="task-detail__grid">
          <div className="task-detail__field">
            <label className="task-detail__field-label">Current Retries</label>
            <p className="task-detail__field-value mono">{task.retry_count}</p>
          </div>
          <div className="task-detail__field">
            <label className="task-detail__field-label">Max Retries</label>
            <p className="task-detail__field-value mono">{task.max_retries}</p>
          </div>
        </div>
      </section>

      {task.required_skills && task.required_skills.length > 0 && (
        <section className="task-detail__section">
          <h2 className="task-detail__section-title">Required Skills</h2>
          <div className="tags-container">
            {task.required_skills.map((skill, index) => (
              <span key={index} className="tag">{skill}</span>
            ))}
          </div>
        </section>
      )}

      {task.acceptance_criteria && task.acceptance_criteria.length > 0 && (
        <section className="task-detail__section">
          <h2 className="task-detail__section-title">Acceptance Criteria</h2>
          <ul className="task-detail__criteria-list">
            {task.acceptance_criteria.map((criterion, index) => (
              <li key={index} className="task-detail__criteria-item">
                <span className="task-detail__criteria-icon">✓</span>
                {criterion}
              </li>
            ))}
          </ul>
        </section>
      )}

      {task.dependencies && task.dependencies.length > 0 && (
        <section className="task-detail__section">
          <h2 className="task-detail__section-title">Dependencies</h2>
          <div className="tags-container">
            {task.dependencies.map((depId, index) => (
              <span key={index} className="tag tag--outline mono">{depId.slice(0, 8)}...</span>
            ))}
          </div>
        </section>
      )}

      {task.error && (
        <section className="task-detail__section">
          <h2 className="task-detail__section-title">Error</h2>
          <div className="alert alert-error">
            <code className="mono">{task.error}</code>
          </div>
        </section>
      )}

      {task.metadata && Object.keys(task.metadata).length > 0 && (
        <section className="task-detail__section">
          <h2 className="task-detail__section-title">Metadata</h2>
          <pre className="task-detail__metadata mono">
            {JSON.stringify(task.metadata, null, 2)}
          </pre>
        </section>
      )}

      <footer className="task-detail__actions">
        {possibleTransitions.length > 0 && (
          <div className="task-detail__status-controls">
            <label className="label">Update Status:</label>
            <select
              className="input select"
              value=""
              onChange={(e) => e.target.value && handleStatusChange(e.target.value)}
              aria-label="Change task status"
            >
              <option value="">Select new status...</option>
              {possibleTransitions.map((status) => (
                <option key={status} value={status}>
                  {status.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </div>
        )}
        <button className="btn btn-outline" onClick={() => navigate(-1)}>
          Back
        </button>
      </footer>
    </div>
  );
};

export default TaskDetail;