import React, { useState, useEffect } from "react";
import { Project, ProjectCreate, TaskStatus, AgentRole, Priority } from "../types";
import { projectApi } from "../services/api";
import Loading from "./Loading";
import "./ProjectList.css";

interface ProjectCardProps {
  project: Project;
  onClick: () => void;
}

const ProjectCard: React.FC<ProjectCardProps> = ({ project, onClick }) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <article className="project-card" onClick={onClick} tabIndex={0} role="button" onKeyDown={(e) => e.key === "Enter" && onClick()}>
      <header className="project-card__header">
        <h3 className="project-card__name">{project.name}</h3>
        <span className="project-card__status">{project.status}</span>
      </header>
      <p className="project-card__description">{project.description || "No description provided"}</p>
      <footer className="project-card__footer">
        <div className="project-card__meta">
          <span className="project-card__meta-item">
            <span className="project-card__meta-label">Created</span>
            <span className="project-card__meta-value">{formatDate(project.created_at)}</span>
          </span>
          <span className="project-card__meta-item">
            <span className="project-card__meta-label">Owner</span>
            <span className="project-card__meta-value">{project.owner_id.slice(0, 8)}...</span>
          </span>
        </div>
        <button className="project-card__action" onClick={(e) => { e.stopPropagation(); onClick(); }}>
          Open Project
        </button>
      </footer>
    </article>
  );
};

interface ProjectListProps {
  onProjectSelect?: (project: Project) => void;
}

const ProjectList: React.FC<ProjectListProps> = ({ onProjectSelect }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [newProject, setNewProject] = useState<ProjectCreate>({
    name: "",
    description: "",
    owner_id: "current-user", // Will come from auth context in Phase 3
    ai_provider: null,
    ai_model: null,
    preferred_language: "en",
    timezone: "UTC",
    telegram_notifications_enabled: false,
    telegram_chat_id: null,
  });

  const fetchProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await projectApi.getAll();
      const list = Array.isArray(data)
        ? data
        : Array.isArray((data as any)?.projects)
        ? (data as any).projects
        : Array.isArray((data as any)?.items)
        ? (data as any).items
        : [];
      setProjects(list);
    } catch (err: any) {
      setError(err.detail || "Failed to load projects");
      setProjects([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setCreateLoading(true);
      setCreateError(null);
      const project = await projectApi.create(newProject);
      setShowCreateModal(false);
      setNewProject({
        name: "",
        description: "",
        owner_id: "current-user",
        ai_provider: null,
        ai_model: null,
        preferred_language: "en",
        timezone: "UTC",
        telegram_notifications_enabled: false,
        telegram_chat_id: null,
      });
      fetchProjects(); // Refresh list
    } catch (err: any) {
      setCreateError(err.detail || "Failed to create project");
    } finally {
      setCreateLoading(false);
    }
  };

  const handleInputChange = (field: keyof ProjectCreate, value: any) => {
    setNewProject((prev) => ({ ...prev, [field]: value }));
  };

  if (loading) {
    return <Loading message="Loading projects..." />;
  }

  return (
    <div className="project-list">
      <header className="project-list__header">
        <h1 className="project-list__title">Projects</h1>
        <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
          <svg className="btn__icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          New Project
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
          <button className="alert__dismiss" onClick={() => { setError(null); fetchProjects(); }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      )}

      {(projects || []).length === 0 && !error && (
        <div className="empty-state">
          <svg className="empty-state__icon" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M21 19V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2z"></path>
            <line x1="9" y1="9" x2="15" y2="15"></line>
            <line x1="15" y1="9" x2="9" y2="15"></line>
          </svg>
          <h2 className="empty-state__title">No Projects Yet</h2>
          <p className="empty-state__description">Create your first project to start building with NexusForge.</p>
          <button className="btn btn-primary empty-state__action" onClick={() => setShowCreateModal(true)}>
            Create Project
          </button>
        </div>
      )}

      {(projects || []).length > 0 && (
        <div className="project-list__grid" role="list">
          {(projects || []).map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onClick={() => onProjectSelect?.(project)}
            />
          ))}
        </div>
      )}

      {/* Create Project Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)} role="dialog" aria-modal="true" aria-labelledby="create-project-title">
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <header className="modal__header">
              <h2 id="create-project-title" className="modal__title">Create New Project</h2>
              <button className="modal__close" onClick={() => setShowCreateModal(false)} aria-label="Close">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </header>
            <form onSubmit={handleCreateProject} className="modal__body" noValidate>
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
                <label htmlFor="project-name" className="label">Project Name *</label>
                <input
                  type="text"
                  id="project-name"
                  className="input"
                  value={newProject.name}
                  onChange={(e) => handleInputChange("name", e.target.value)}
                  required
                  placeholder="My AI Project"
                  autoFocus
                />
              </div>

              <div className="form-group">
                <label htmlFor="project-description" className="label">Description *</label>
                <textarea
                  id="project-description"
                  className="input textarea"
                  value={newProject.description}
                  onChange={(e) => handleInputChange("description", e.target.value)}
                  required
                  placeholder="Describe what this project will build..."
                  rows={4}
                />
              </div>

              <div className="form-group">
                <label htmlFor="project-language" className="label">Preferred Language</label>
                <select
                  id="project-language"
                  className="input select"
                  value={newProject.preferred_language}
                  onChange={(e) => handleInputChange("preferred_language", e.target.value)}
                >
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                  <option value="zh">Chinese</option>
                  <option value="ja">Japanese</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="project-timezone" className="label">Timezone</label>
                <select
                  id="project-timezone"
                  className="input select"
                  value={newProject.timezone}
                  onChange={(e) => handleInputChange("timezone", e.target.value)}
                >
                  <option value="UTC">UTC</option>
                  <option value="America/New_York">Eastern Time</option>
                  <option value="America/Chicago">Central Time</option>
                  <option value="America/Denver">Mountain Time</option>
                  <option value="America/Los_Angeles">Pacific Time</option>
                  <option value="Europe/London">London</option>
                  <option value="Europe/Paris">Paris</option>
                  <option value="Asia/Tokyo">Tokyo</option>
                  <option value="Asia/Shanghai">Shanghai</option>
                </select>
              </div>

              <footer className="modal__footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={createLoading || !newProject.name.trim() || !newProject.description.trim()}>
                  {createLoading ? (
                    <>
                      <span className="loading-spinner" style={{ width: "16px", height: "16px" }}></span>
                      Creating...
                    </>
                  ) : (
                    "Create Project"
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

export { ProjectList };
export default ProjectList;
