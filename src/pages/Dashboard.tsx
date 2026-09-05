import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Project, HealthResponse } from "../types";
import { healthApi, projectApi } from "../services/api";
import "./Dashboard.css";

const Dashboard: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [healthData, projectsData] = await Promise.all([
        healthApi.check(),
        projectApi.getAll(),
      ]);
      setHealth(healthData);
      setProjects(projectsData);
    } catch (err: any) {
      setError(err.detail || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
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
        <button className="btn btn-primary" onClick={fetchDashboardData}>
          <RefreshIcon />
          Refresh
        </button>
      </header>

      <div className="dashboard__content">
        {/* Health & Status Section */}
        <section className="dashboard__section">
          <h2 className="dashboard__section-title">System Status</h2>
          <div className="dashboard__health-grid">
            <HealthCard
              label="API"
              status={health?.status === "ok" ? "Healthy" : "Error"}
              icon={health?.status === "ok" ? "✅" : "❌"}
            />
            <HealthCard
              label="Database"
              status={health?.checks?.database ? "Connected" : "Error"}
              icon={health?.checks?.database ? "✅" : "❌"}
            />
            <HealthCard
              label="Redis"
              status={health?.checks?.redis ? "Connected" : "Error"}
              icon={health?.checks?.redis ? "✅" : "❌"}
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
        <button className="btn btn-outline" disabled title="Coming in Phase 5.5">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 11h6"></path>
            <path d="M12 8v8"></path>
            <circle cx="12" cy="12" r="9"></circle>
          </svg>
          New Task
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