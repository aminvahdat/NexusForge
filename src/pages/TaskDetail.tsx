import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Task, Project, ExecutionEvent, WebSocketMessage } from "../types";
import { taskApi, projectApi, executionApi } from "../services/api";
import { ExecutionStatus } from "../components/ExecutionStatus";
import { ExecutionTimeline } from "../components/ExecutionTimeline";
import Loading from "../components/Loading";
import "./TaskDetail.css";

const TaskDetail: React.FC = () => {
  const { projectId, taskId } = useParams<{ projectId: string; taskId: string }>();
  const navigate = useNavigate();
  const [task, setTask] = useState<Task | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Execution state
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [executionStatus, setExecutionStatus] = useState<string>("");
  const [executionEvents, setExecutionEvents] = useState<ExecutionEvent[]>([]);
  const [executionError, setExecutionError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      if (!taskId || !projectId) return;
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
  }, [taskId, projectId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // WebSocket connection for real-time events
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [wsReconnecting, setWsReconnecting] = useState(false);

  useEffect(() => {
    if (!executionId) return;

    let websocket: WebSocket | null = null;
    try {
      const wsProto = window.location.protocol === "https:" ? "wss" : "ws";
      const wsUrl = `${wsProto}://${window.location.host}/execution/ws/${executionId}`;
      websocket = new WebSocket(wsUrl);
      setWs(websocket);

      websocket.onopen = () => {
        setWsConnected(true);
        setWsReconnecting(false);
        console.log("WebSocket connected for execution", executionId);
      };

      websocket.onmessage = (event) => {
        try {
          const msg: WebSocketMessage = JSON.parse(event.data);
          if (msg.type === "execution_event" && msg.event) {
            setExecutionEvents((prev) => {
              // Prevent duplicates by event timestamp + type
              const exists = prev.some(
                (e) =>
                  e.event_type === msg.event.event_type &&
                  e.timestamp === msg.event.timestamp
              );
              if (exists) return prev;
              return [...prev, msg.event];
            });
          } else if (msg.type === "state_sync") {
            // Handle initial state sync
          }
        } catch (e) {
          console.warn("Failed to parse WebSocket message:", e);
        }
      };

      websocket.onerror = (err) => {
        console.error("WebSocket error:", err);
        setWsConnected(false);
      };

      websocket.onclose = () => {
        console.log("WebSocket disconnected");
        setWsConnected(false);
        // Auto reconnect after a short delay
        setWsReconnecting(true);
        setTimeout(() => {
          if (executionId) {
            setWsReconnecting(false);
            // Reconnect handled by effect re-run if executionId changes
          }
        }, 2000);
      };
    } catch (err) {
      console.warn("Failed to connect WebSocket for execution:", err);
      setWsConnected(false);
    }

    return () => {
      if (websocket) {
        try {
          websocket.close();
        } catch {
          // ignore
        }
      }
      setWs(null);
    };
  }, [executionId]);

  // Poll execution status (as fallback and initial check)
  useEffect(() => {
    if (!executionId) return;

    const pollStatus = async () => {
      try {
        const statusData = await executionApi.status(executionId);
        setExecutionStatus(statusData.status);
      } catch (err) {
        console.warn("Failed to poll execution status:", err);
      }
    };

    pollStatus();
    const interval = setInterval(pollStatus, 3000);
    return () => clearInterval(interval);
  }, [executionId]);

  const handleStartExecution = async () => {
    if (!taskId) return;
    try {
      const result = await executionApi.start(taskId);
      setExecutionId(result.execution_id);
      setExecutionStatus(result.status);
      setExecutionEvents(result.event ? [result.event] : []);
      setExecutionError(null);
    } catch (err: any) {
      setError(err.detail || "Failed to start execution");
    }
  };

  const handleCancelExecution = async () => {
    if (!executionId) return;
    try {
      const result = await executionApi.cancel(executionId);
      setExecutionStatus(result.status || "cancelled");
      setExecutionError(null);
      await fetchData();
    } catch (err: any) {
      setExecutionError(err.detail || "Failed to cancel execution");
    }
  };

  const handlePauseExecution = async () => {
    if (!executionId) return;
    try {
      const result = await executionApi.pause(executionId);
      setExecutionStatus(result.status || "paused");
      setExecutionError(null);
    } catch (err: any) {
      const msg = err.detail || (err.response && err.response.data && err.response.data.detail) || "Failed to pause execution";
      setExecutionError(msg);
    }
  };

  const handleResumeExecution = async () => {
    if (!executionId) return;
    try {
      const result = await executionApi.resume(executionId);
      setExecutionStatus(result.status || "running");
      setExecutionError(null);
    } catch (err: any) {
      const msg = err.detail || (err.response && err.response.data && err.response.data.detail) || "Failed to resume execution";
      setExecutionError(msg);
    }
  };

  const handleStatusChange = async (newStatus: string) => {
    try {
      const updated = await taskApi.update(taskId!, { status: newStatus });
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
    return role.replace(/_/, " ").replace(/\b\w/g, (l) => l.toUpperCase());
  };

  if (loading) {
    return <Loading message="Loading task..." />;
  }

  if (error && !executionId) {
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
        <div className="alert alert-error" role="alert">Task or project not found.</div>
      </div>
    );
  }

  const canTransitionTo = (newStatus: string) => {
    const terminal = ["completed", "failed", "cancelled"];
    if (terminal.includes(task.status)) return false;
    return newStatus !== task.status;
  };

  const possibleTransitions = [
    "queued", "planning", "ready", "running", "waiting", "reviewing", "completed", "failed", "cancelled",
  ].filter((status) => canTransitionTo(status) && status !== "queued");

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

      {/* Execution Monitoring Section */}
      <section className="task-detail__section task-detail__execution">
        <h2 className="task-detail__section-title">Execution Monitoring</h2>
        <div className="execution-monitor">
          <div className="execution-monitor__header">
            <h3>Live Execution</h3>
            {!executionId ? (
              <button className="btn btn-primary btn-sm" onClick={handleStartExecution}>
                Start Execution
              </button>
            ) : (
              <div className="execution-monitor__status-row" style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
                <ExecutionStatus status={executionStatus} error={executionError || undefined} />
                <span className="execution-monitor__execution-id">ID: {executionId}</span>
                <span className={`execution-monitor__connection ${wsConnected ? "connected" : wsReconnecting ? "reconnecting" : "disconnected"}`}>
                  {wsConnected ? "● Live" : wsReconnecting ? "↻ Reconnecting" : "○ Offline"}
                </span>
                <div className="execution-monitor__actions" style={{ display: "flex", gap: "8px", marginLeft: "auto" }}>
                  {executionStatus === "paused" ? (
                    <button
                      className="btn btn-outline btn-sm"
                      onClick={handleResumeExecution}
                      title="Resume suspended process (POSIX only)"
                    >
                      Resume
                    </button>
                  ) : executionStatus === "running" ? (
                    <button
                      className="btn btn-outline btn-sm"
                      onClick={handlePauseExecution}
                      title="Suspend process execution (Windows returns 501 Not Implemented; use Cancel instead)"
                    >
                      Pause
                    </button>
                  ) : null}
                  {["running", "paused", "waiting", "queued"].includes(executionStatus) && (
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={handleCancelExecution}
                      title="Terminate execution process tree immediately"
                    >
                      Cancel Execution
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>

          {executionError && (
            <div className="alert alert-warning" style={{ margin: "10px 0", fontSize: "0.88rem" }} role="alert">
              <strong>Execution Notice:</strong> {executionError}
              {executionError.includes("Windows") && (
                <div style={{ marginTop: "4px", color: "var(--color-text-muted)" }}>
                  💡 On Windows host systems, native process freezing (SIGSTOP/SIGCONT) is unavailable. Click <strong>Cancel Execution</strong> to terminate the process cleanly.
                </div>
              )}
            </div>
          )}

          {executionId && (
            <>
              <div className="execution-monitor__info">
                <div className="execution-info__row">
                  <span className="label">Task:</span>
                  <span className="mono">{task.id.slice(0, 8)}...</span>
                </div>
                <div className="execution-info__row">
                  <span className="label">Status:</span>
                  <span className="mono">{executionStatus || "-"}</span>
                </div>
                <div className="execution-info__row">
                  <span className="label">Worker:</span>
                  <span className="mono">{executionEvents.find((e) => e.event_type === "WORKER_ASSIGNED")?.worker_id || task.assigned_worker || "Not assigned"}</span>
                </div>
                <div className="execution-info__row">
                  <span className="label">Events:</span>
                  <span className="mono">{executionEvents.length}</span>
                </div>
              </div>

              <ExecutionTimeline events={executionEvents} />
            </>
          )}
        </div>
      </section>

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