import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Project, HealthResponse, ExecutionEvent, WebSocketMessage } from "../types";
import { healthApi, projectApi, executionsApi } from "../services/api";
import { ExecutionStatus } from "../components/ExecutionStatus";
import { Toast } from "../components/Toast";
import { Skeleton } from "../components/Skeleton";
import "./Dashboard.css";

const Dashboard: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeExecutions, setActiveExecutions] = useState(0);
  const [recentEvents, setRecentEvents] = useState<ExecutionEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [toast, setToast] = useState<{
    type: "success" | "error" | "info";
    title: string;
    message: string;
  } | null>(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [healthData, projectsData, eventsData] = await Promise.all([
        healthApi.check(),
        projectApi.getAll(),
        executionsApi.list(),
      ]);
      setHealth(healthData);
      setProjects(projectsData);
      setRecentEvents(eventsData.slice(0, 5));
      setActiveExecutions(
        eventsData.filter(
          (e: ExecutionEvent) =>
            e.event_type === "EXECUTION_STARTED" || e.execution_status === "running"
        ).length
      );
    } catch (err: any) {
      setError(err.detail || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // WebSocket for real-time updates
  useEffect(() => {
    const clientId = "dashboard-" + Date.now();
    const ws = new WebSocket(
      `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/execution/ws/${clientId}`
    );

    ws.onopen = () => setWsConnected(true);
    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        if (message.type === "execution_event" && message.data) {
          const newEvent = message.data as ExecutionEvent;
          setRecentEvents((prev) => {
            const exists = prev.some(
              (e) =>
                e.event_type === newEvent.event_type &&
                e.timestamp === newEvent.timestamp &&
                e.worker_id === newEvent.worker_id
            );
            if (exists) return prev;
            return [newEvent, ...prev].slice(0, 5);
          });
        } else if (message.type === "execution_complete" || message.type === "execution_failed") {
          setToast({
            type: message.type === "execution_complete" ? "success" : "error",
            title: message.type === "execution_complete" ? "Execution Complete" : "Execution Failed",
            message: `An execution just ${message.type === "execution_complete" ? "completed" : "failed"}.`,
          });
        }
      } catch {
        // Ignore parse errors
      }
    };
    ws.onerror = () => setWsConnected(false);
    ws.onclose = () => setWsConnected(false);

    return () => ws.close();
  }, []);

  const recentProjects = projects.slice(0, 5);

  return (
    <div className="dashboard">
      <header className="dashboard__header">
        <div className="dashboard__title-section">
          <h1 className="dashboard__title">NexusForge Dashboard</h1>
          <p className="dashboard__subtitle">
            Your autonomous software development workspace
          </p>
        </div>
        <div className="dashboard__header-actions">
          <ExecutionStatus
            status={wsConnected ? "running" : "disconnected"}
            isLive={wsConnected}
            connected={wsConnected}
            onRefresh={fetchDashboardData}
          />
          <button className="btn btn-primary" onClick={fetchDashboardData}>
            <RefreshIcon />
            Refresh
          </button>
        </div>
      </header>

      {toast && (
        <Toast
          type={toast.type}
          title={toast.title}
          message={toast.message}
          onClose={() => setToast(null)}
        />
      )}

      <div className="dashboard__content">
        {/* Real-time Activity Section */}
        <section className="dashboard__section">
          <h2 className="dashboard__section-title">Real-Time Activity</h2>
          <div className="dashboard__activity-stats">
            <div className="dashboard__activity-card">
              <h3 className="dashboard__activity-value">{activeExecutions}</h3>
              <p className="dashboard__activity-label">Active Executions</p>
            </div>
            <div className="dashboard__activity-card">
              <h3 className="dashboard__activity-value">{recentEvents.length}</h3>
              <p className="dashboard__activity-label">Recent Events</p>
            </div>
          </div>
        </section>

        {/* Health & Status Section */}
        <section className="dashboard__section">
          <h2 className="dashboard__section-title">System Status</h2>
          <div className="dashboard__health-grid">
            <HealthCard
              label="API"
              status={health?.status === "ok" ? "Healthy" : "Error"}
              icon={health?.status === "ok" ? "✓" : "✗"}
            />
            <HealthCard
              label="Database"
              status={health?.checks?.database ? "Connected" : "Error"}
              icon={health?.checks?.database ? "✓" : "✗"}
            />
            <HealthCard
              label="Redis"
              status={health?.checks?.redis ? "Connected" : "Error"}
              icon={health?.checks?.redis ? "✓" : "✗"}
            />
          </div>
        </section>

        {/* Projects Section */}
        <section className="dashboard__section">
          <div className="dashboard__section-header">
            <h2 className="dashboard__section-title">Recent Projects</h2>
            <button className="btn btn-outline btn-sm" onClick={() => window.location.assign("/projects")}>
              View All
            </button>
          </div>

          {recentProjects.length > 0 ? (
            <div className="dashboard__projects">
              {recentProjects.map((project) => (
                <div
                  key={project.id}
                  className="dashboard__project-item"
                  onClick={() => window.location.assign(`/projects/${project.id}`)}
                >
                  <div>
                    <h3 className="dashboard__project-name">{project.name}</h3>
                    <p className="dashboard__project-desc">
                      {project.description || "No description"}
                    </p>
                  </div>
                  <span className="dashboard__project-status">{project.status}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <svg className="empty-state__icon" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M22 19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l2 3h9a2 2 0 0 1 2 2v11z"></path>
              </svg>
              <h3 className="empty-state__title">No Projects Yet</h3>
              <p className="empty-state__description">
                Create your first project to start building with NexusForge.
              </p>
              <button className="btn btn-primary" onClick={() => window.location.assign("/projects")}>
                Go to Projects
              </button>
            </div>
          )}
        </section>
      </div>

      {/* Quick Actions */}
      <aside className="dashboard__quick-actions">
        <button className="btn btn-outline" onClick={() => window.location.assign("/activity")}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
          View Activity
        </button>
        <button className="btn btn-outline" onClick={() => window.location.assign("/workers")}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="2" y="2" width="20" height="8" rx="2"></rect>
            <rect x="2" y="14" width="20" height="8" rx="2"></rect>
          </svg>
          View Workers
        </button>
      </aside>
    </div>
  );
};

function HealthCard({ label, status, icon }: { label: string; status: string; icon: string }) {
  return (
    <div className="health-card">
      <span className="health-card__icon">{icon}</span>
      <div>
        <p className="health-card__label">{label}</p>
        <p className="health-card__status">{status}</p>
      </div>
    </div>
  );
}

function RefreshIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="4 12v8h8"></polyline>
      <path d="M10 14l4 4 4-4"></path>
    </svg>
  );
}

export default Dashboard;