import React, { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Project, ProjectCreate } from "../types";
import { projectApi } from "../services/api";
import { useLanguage } from "../context/LanguageContext";
import Loading from "../components/Loading";
import "./ProjectList.css";

type TabType = "active" | "archived" | "all";

const ProjectListPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>("active");
  const [searchQuery, setSearchQuery] = useState("");

  // Create Project Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [newProject, setNewProject] = useState<ProjectCreate>({
    name: "",
    description: "",
    owner_id: "current-user",
    ai_provider: "anthropic",
    ai_model: "claude-3-7-sonnet-latest",
    preferred_language: "fa",
    timezone: "UTC",
    telegram_notifications_enabled: false,
    telegram_chat_id: null,
    workspace_path: "",
  });

  // Delete Confirmation Modal
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Action Loading states (by project id)
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  const navigate = useNavigate();
  const { t, lang, isRTL } = useLanguage();

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
      setError(err.detail || t("common.error"));
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
    if (!newProject.name.trim()) return;

    try {
      setCreateLoading(true);
      setCreateError(null);
      const created = await projectApi.create(newProject);
      setShowCreateModal(false);
      try {
        await projectApi.run(created.id);
      } catch (runErr) {
        console.warn("Auto-run trigger:", runErr);
      }
      navigate(`/projects/${created.id}`);
    } catch (err: any) {
      setCreateError(err.detail || t("common.error"));
    } finally {
      setCreateLoading(false);
    }
  };

  const handleToggleArchive = async (e: React.MouseEvent, project: Project) => {
    e.stopPropagation();
    try {
      setActionLoadingId(project.id);
      if (project.status === "archived") {
        await projectApi.unarchive(project.id);
      } else {
        await projectApi.archive(project.id);
      }
      await fetchProjects();
    } catch (err: any) {
      alert(err.detail || "Failed to update project archive status");
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!projectToDelete) return;
    try {
      setDeleteLoading(true);
      await projectApi.delete(projectToDelete.id);
      setProjectToDelete(null);
      await fetchProjects();
    } catch (err: any) {
      alert(err.detail || "Failed to delete project");
    } finally {
      setDeleteLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString(lang === "fa" ? "fa-IR" : "en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return dateString;
    }
  };

  // Filtered lists
  const counts = useMemo(() => {
    const active = projects.filter((p) => p.status !== "archived").length;
    const archived = projects.filter((p) => p.status === "archived").length;
    return { active, archived, all: projects.length };
  }, [projects]);

  const filteredProjects = useMemo(() => {
    return projects.filter((p) => {
      // Tab filter
      if (activeTab === "active" && p.status === "archived") return false;
      if (activeTab === "archived" && p.status !== "archived") return false;

      // Search query filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchName = (p.name || "").toLowerCase().includes(q);
        const matchDesc = (p.description || "").toLowerCase().includes(q);
        return matchName || matchDesc;
      }
      return true;
    });
  }, [projects, activeTab, searchQuery]);

  if (loading) {
    return <Loading message={t("common.loading")} />;
  }

  return (
    <div className="projects-page">
      {/* Header */}
      <header className="projects-header">
        <div className="projects-header__title-group">
          <h1>{t("projects.title")}</h1>
          <p>{t("projects.subtitle")}</p>
        </div>
        <div className="projects-header__actions">
          <button className="btn-new-project" onClick={() => setShowCreateModal(true)}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            <span>{t("projects.new_btn")}</span>
          </button>
        </div>
      </header>

      {/* Controls Bar: Tabs & Search */}
      <div className="projects-controls">
        <div className="projects-tabs">
          <button
            className={`projects-tab-btn ${activeTab === "active" ? "projects-tab-btn--active" : ""}`}
            onClick={() => setActiveTab("active")}
          >
            <span>{t("projects.tab_active")}</span>
            <span className="projects-tab-badge">{counts.active}</span>
          </button>
          <button
            className={`projects-tab-btn ${activeTab === "archived" ? "projects-tab-btn--active" : ""}`}
            onClick={() => setActiveTab("archived")}
          >
            <span>{t("projects.tab_archived")}</span>
            <span className="projects-tab-badge">{counts.archived}</span>
          </button>
          <button
            className={`projects-tab-btn ${activeTab === "all" ? "projects-tab-btn--active" : ""}`}
            onClick={() => setActiveTab("all")}
          >
            <span>{t("projects.tab_all")}</span>
            <span className="projects-tab-badge">{counts.all}</span>
          </button>
        </div>

        <div className="projects-search-box">
          <svg className="projects-search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input
            type="text"
            className="projects-search-input"
            placeholder={t("projects.search_placeholder")}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {error && (
        <div className="alert alert-error" role="alert" style={{ marginBottom: "1.5rem" }}>
          <span>{error}</span>
          <button className="alert__dismiss" onClick={() => { setError(null); fetchProjects(); }}>✕</button>
        </div>
      )}

      {/* Projects Grid or Empty State */}
      {filteredProjects.length === 0 ? (
        <div className="projects-empty-state">
          <div className="projects-empty-icon">📁</div>
          <h3>{t("projects.empty_title")}</h3>
          <p>{t("projects.empty_desc")}</p>
          <button className="btn-new-project" onClick={() => setShowCreateModal(true)}>
            {t("projects.new_btn")}
          </button>
        </div>
      ) : (
        <div className="projects-grid">
          {filteredProjects.map((project) => {
            const isArchived = project.status === "archived";
            const isActionBusy = actionLoadingId === project.id;

            return (
              <article
                key={project.id}
                className={`project-card ${isArchived ? "project-card--archived" : ""}`}
                onClick={() => navigate(`/projects/${project.id}`)}
                tabIndex={0}
              >
                <header className="project-card__header">
                  <h2 className="project-card__title">{project.name}</h2>
                  <span
                    className={`project-status-pill ${
                      isArchived ? "project-status-pill--archived" : "project-status-pill--active"
                    }`}
                  >
                    {isArchived ? t("projects.status_archived") : t("projects.status_active")}
                  </span>
                </header>

                <div className="project-card__body">
                  <p className="project-card__desc">
                    {project.description || (lang === "fa" ? "بدون توضیحات ثبت‌شده" : "No description provided")}
                  </p>

                  <div className="project-card__tags">
                    {project.preferred_language && (
                      <span className="project-card-tag" title={t("projects.badge_lang")}>
                        <span className="project-card-tag__icon">🌐</span>
                        <span>{project.preferred_language === "fa" ? "فارسی" : "English"}</span>
                      </span>
                    )}
                    {project.ai_provider && (
                      <span className="project-card-tag" title={t("projects.badge_provider")}>
                        <span className="project-card-tag__icon">⚡</span>
                        <span style={{ textTransform: "capitalize" }}>{project.ai_provider}</span>
                      </span>
                    )}
                    {project.ai_model && (
                      <span className="project-card-tag" title={t("projects.badge_model")}>
                        <span className="project-card-tag__icon">🧠</span>
                        <span>{project.ai_model}</span>
                      </span>
                    )}
                  </div>
                </div>

                <footer className="project-card__footer" onClick={(e) => e.stopPropagation()}>
                  <div className="project-card__meta-date">
                    <span>{t("projects.created_at")} {formatDate(project.created_at)}</span>
                  </div>

                  <div className="project-card__actions">
                    {/* Archive / Unarchive Button */}
                    <button
                      type="button"
                      className="btn-card-action"
                      disabled={isActionBusy}
                      onClick={(e) => handleToggleArchive(e, project)}
                      title={isArchived ? t("projects.action_unarchive") : t("projects.action_archive")}
                    >
                      {isArchived ? (
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <polyline points="9 11 12 14 22 4"></polyline>
                          <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
                        </svg>
                      ) : (
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <polyline points="21 8 21 21 3 21 3 8"></polyline>
                          <rect x="1" y="3" width="22" height="5"></rect>
                          <line x1="10" y1="12" x2="14" y2="12"></line>
                        </svg>
                      )}
                    </button>

                    {/* Delete Button */}
                    <button
                      type="button"
                      className="btn-card-action btn-card-action--danger"
                      onClick={(e) => {
                        e.stopPropagation();
                        setProjectToDelete(project);
                      }}
                      title={t("projects.action_delete")}
                    >
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        <line x1="10" y1="11" x2="10" y2="17"></line>
                        <line x1="14" y1="11" x2="14" y2="17"></line>
                      </svg>
                    </button>

                    {/* Open Project CTA */}
                    <button
                      type="button"
                      className="btn-card-open"
                      onClick={() => navigate(`/projects/${project.id}`)}
                    >
                      {t("projects.action_open")} →
                    </button>
                  </div>
                </footer>
              </article>
            );
          })}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {projectToDelete && (
        <div className="modal-overlay" onClick={() => setProjectToDelete(null)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <header className="modal-dialog__header">
              <h3>{t("projects.delete_confirm_title")}</h3>
              <button className="modal-dialog__close-btn" onClick={() => setProjectToDelete(null)}>✕</button>
            </header>
            <div className="modal-dialog__body">
              <p style={{ color: "#F0F4F8", fontWeight: 600, marginBottom: "0.5rem" }}>
                «{projectToDelete.name}»
              </p>
              <p style={{ color: "#8E95A5", fontSize: "0.9rem", lineHeight: 1.5 }}>
                {t("projects.delete_confirm_desc")}
              </p>
            </div>
            <footer className="modal-dialog__footer">
              <button
                type="button"
                className="btn-secondary"
                disabled={deleteLoading}
                onClick={() => setProjectToDelete(null)}
              >
                {t("common.cancel")}
              </button>
              <button
                type="button"
                className="btn-danger"
                disabled={deleteLoading}
                onClick={handleDeleteConfirm}
              >
                {deleteLoading ? t("common.loading") : t("projects.action_delete")}
              </button>
            </footer>
          </div>
        </div>
      )}

      {/* Create Project Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-dialog" style={{ maxWidth: "560px" }} onClick={(e) => e.stopPropagation()}>
            <header className="modal-dialog__header">
              <h3>{t("modal.create_project_title")}</h3>
              <button className="modal-dialog__close-btn" onClick={() => setShowCreateModal(false)}>✕</button>
            </header>
            <form onSubmit={handleCreateProject}>
              <div className="modal-dialog__body">
                {createError && (
                  <div className="alert alert-error" style={{ marginBottom: "1rem" }}>
                    <span>{createError}</span>
                  </div>
                )}

                <div className="form-group" style={{ marginBottom: "1.2rem" }}>
                  <label className="label">{t("modal.project_name")} *</label>
                  <input
                    type="text"
                    className="input"
                    required
                    placeholder={lang === "fa" ? "مثال: سامانه پرداخت کریپتو" : "e.g. Autonomous Payment Gateway"}
                    value={newProject.name}
                    onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                  />
                </div>

                <div className="form-group" style={{ marginBottom: "1.2rem" }}>
                  <label className="label">{t("modal.project_desc")}</label>
                  <textarea
                    className="input"
                    rows={3}
                    placeholder={lang === "fa" ? "شرح معماری، اهداف و تکنولوژی‌های مورد نیاز..." : "Describe goals, architecture, tech stack..."}
                    value={newProject.description}
                    onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                  />
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1.2rem" }}>
                  <div className="form-group">
                    <label className="label">{t("modal.ai_provider")}</label>
                    <select
                      className="input"
                      value={newProject.ai_provider || "anthropic"}
                      onChange={(e) => setNewProject({ ...newProject, ai_provider: e.target.value })}
                    >
                      <option value="anthropic">Anthropic (Claude 3.7 / 3.5)</option>
                      <option value="openai">OpenAI (o3-mini / GPT-4o)</option>
                      <option value="deepseek">DeepSeek (R1 Reasoning)</option>
                      <option value="google">Google Gemini (2.5 Pro)</option>
                      <option value="ollama">Ollama (Local Models)</option>
                      <option value="groq">Groq (Ultra-Fast)</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="label">{t("modal.preferred_lang")}</label>
                    <select
                      className="input"
                      value={newProject.preferred_language}
                      onChange={(e) => setNewProject({ ...newProject, preferred_language: e.target.value })}
                    >
                      <option value="fa">فارسی (Persian)</option>
                      <option value="en">English (US)</option>
                    </select>
                  </div>
                </div>

                <div className="form-group" style={{ marginBottom: "1.2rem" }}>
                  <label className="label">
                    {lang === "fa" ? "📁 مسیر پوشه و ورک‌اسپیس پروژه (اختیاری)" : "📁 Project Workspace Directory (Optional)"}
                  </label>
                  <input
                    type="text"
                    className="input"
                    dir="ltr"
                    placeholder={lang === "fa" ? "پیش‌فرض: workspaces/{project_id} یا مسیر دلخواه مثل E:\\projects\\app" : "Default: workspaces/{project_id} or custom path like E:\\projects\\app"}
                    value={newProject.workspace_path || ""}
                    onChange={(e) => setNewProject({ ...newProject, workspace_path: e.target.value })}
                  />
                  <span style={{ fontSize: "0.75rem", color: "#8E95A5", marginTop: "4px", display: "block" }}>
                    {lang === "fa"
                      ? "فایل‌های تولیدشده و دستورات شل ترمینال در این فولدر ذخیره و اجرا خواهند شد."
                      : "Generated files and terminal commands will be executed inside this folder."}
                  </span>
                </div>
              </div>

              <footer className="modal-dialog__footer">
                <button
                  type="button"
                  className="btn-secondary"
                  disabled={createLoading}
                  onClick={() => setShowCreateModal(false)}
                >
                  {t("modal.cancel")}
                </button>
                <button
                  type="submit"
                  className="btn-new-project"
                  disabled={createLoading || !newProject.name.trim()}
                >
                  {createLoading ? t("common.loading") : t("modal.submit")}
                </button>
              </footer>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectListPage;