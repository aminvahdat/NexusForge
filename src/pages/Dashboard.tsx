import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Project, HealthResponse } from "../types";
import { healthApi, projectApi, taskApi } from "../services/api";
import { useLanguage } from "../context/LanguageContext";
import { ToastProvider as Toast } from "../components/Toast";
import "../components/Dashboard.css";

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { lang } = useLanguage();
  const isFa = lang === "fa";

  const [autonomousPrompt, setAutonomousPrompt] = useState("");
  const [isLaunchingPrompt, setIsLaunchingPrompt] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  // New Project Modal State
  const [showNewProjectModal, setShowNewProjectModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectDesc, setNewProjectDesc] = useState("");
  const [newProjectWorkspacePath, setNewProjectWorkspacePath] = useState("");
  const [creatingProject, setCreatingProject] = useState(false);

  const [toast, setToast] = useState<{
    type: "success" | "error" | "info";
    title: string;
    message: string;
  } | null>(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [healthData, projectsData] = await Promise.all([
        healthApi.check().catch(() => null),
        projectApi.getAll().catch(() => []),
      ]);
      setHealth(healthData);
      setProjects(projectsData || []);
    } catch (err: any) {
      console.warn("Failed to load dashboard data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Launch Project Directly via Prompt
  const handleLaunchAutonomousForge = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const promptText = autonomousPrompt.trim();
    if (!promptText || isLaunchingPrompt) return;

    setIsLaunchingPrompt(true);
    try {
      const words = promptText.split(/\s+/).slice(0, 4).join(" ");
      const projName = words.length > 3 ? words : (isFa ? "پروژه هوشمند نکسوس" : "Smart Nexus Project");
      const cleanName = projName.slice(0, 30) + " " + Math.random().toString(36).substring(2, 6);

      // 1. Create project
      const createdProject = await projectApi.create({
        name: cleanName,
        description: promptText,
        owner_id: "current-user",
        ai_provider: "openrouter",
        preferred_language: lang,
      });

      // 2. Create initial project task
      await taskApi.create(createdProject.id, {
        title: isFa ? `راه‌اندازی پروژه: ${cleanName}` : `Initialize: ${cleanName}`,
        description: promptText,
        role: "orchestrator",
        priority: "high",
        status: "queued",
        required_skills: ["architecture", "execution"],
        acceptance_criteria: [
          isFa ? "تحلیل نیازمندی‌ها و سازماندهی فضای کاری" : "Requirements analysis and workspace setup",
          isFa ? "تولید کدهای واقعی و راستی‌آزمایی خروجی" : "Code synthesis and deliverable verification"
        ]
      });

      setAutonomousPrompt("");
      navigate(`/projects/${createdProject.id}`);
    } catch (err: any) {
      setToast({
        type: "error",
        title: isFa ? "خطا در شروع پروژه" : "Launch Failed",
        message: err.detail || err.message || (isFa ? "مشکلی در شروع پروژه رخ داد." : "Could not launch project."),
      });
    } finally {
      setIsLaunchingPrompt(false);
    }
  };

  // Create Project via Modal
  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim() || creatingProject) return;

    setCreatingProject(true);
    try {
      const created = await projectApi.create({
        name: newProjectName.trim(),
        description: newProjectDesc.trim(),
        ai_provider: "openrouter",
        workspace_path: newProjectWorkspacePath.trim() || undefined,
      });
      setShowNewProjectModal(false);
      setNewProjectName("");
      setNewProjectDesc("");
      setNewProjectWorkspacePath("");
      navigate(`/projects/${created.id}`);
    } catch (err: any) {
      setToast({
        type: "error",
        title: isFa ? "خطا در ایجاد پروژه" : "Creation Failed",
        message: err.detail || err.message || (isFa ? "امکان ساخت پروژه وجود ندارد." : "Could not create project."),
      });
    } finally {
      setCreatingProject(false);
    }
  };

  // Delete Project from list
  const handleDeleteProject = async (id: string, name: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm(isFa ? `آیا از حذف پروژه «${name}» اطمینان دارید؟` : `Delete project "${name}"?`)) return;
    try {
      await projectApi.delete(id);
      setProjects((prev) => prev.filter((p) => p.id !== id));
      setToast({
        type: "info",
        title: isFa ? "پروژه حذف شد" : "Project Deleted",
        message: isFa ? `پروژه «${name}» با موفقیت حذف گردید.` : `Project "${name}" was deleted.`,
      });
    } catch (err: any) {
      alert(isFa ? "خطا در حذف پروژه" : "Failed to delete project");
    }
  };

  return (
    <div className={`dashboard ${isFa ? "rtl" : "ltr"}`}>
      {/* Toast */}
      {toast && (
        <Toast
          type={toast.type}
          title={toast.title}
          message={toast.message}
          onClose={() => setToast(null)}
        />
      )}

      {/* 1. WELCOME HEADER */}
      <header className="dashboard__header">
        <div className="dashboard__title-section">
          <h1 className="dashboard__title">
            {isFa ? "سلام! به نکسوس‌فورج خوش آمدید 👋" : "Welcome to NexusForge 👋"}
          </h1>
          <p className="dashboard__subtitle">
            {isFa
              ? "ایده یا تسک خود را بنویسید؛ نکسوس‌فورج مراحل معماری و اجرای واقعی را مدیریت می‌کند."
              : "Describe your project; NexusForge coordinates task execution and deliverables."}
          </p>
        </div>
        <div className="dashboard__header-actions">
          <button className="btn btn-primary" onClick={() => setShowNewProjectModal(true)}>
            <span>+</span>
            <span>{isFa ? "پروژه جدید" : "New Project"}</span>
          </button>
          <button className="btn btn-outline" onClick={fetchDashboardData} title={isFa ? "بروزرسانی" : "Refresh"}>
            🔄
          </button>
        </div>
      </header>

      {/* 2. FRIENDLY HERO PROMPT CARD */}
      <section className="hero-forge-clean">
        <div className="hero-forge-header">
          <span className="hero-tag">⚡ {isFa ? "شروع آنی پروژه" : "Instant Start"}</span>
          <h2 className="hero-title">
            {isFa ? "چه نرم‌افزاری می‌خواهید بسازید؟" : "What software do you want to build today?"}
          </h2>
          <p className="hero-desc">
            {isFa
              ? "کافیست ایده خود را به زبان ساده بنویسید. نکسوس‌فورج تسک‌های پروژه را ایجاد و آماده اجرا می‌کند."
              : "Simply type your objective. NexusForge will structure tasks and prepare execution."}
          </p>
        </div>

        <form onSubmit={handleLaunchAutonomousForge}>
          <div className="hero-input-box">
            <textarea
              className="hero-textarea"
              placeholder={
                isFa
                  ? "ایده یا ویژگی مورد نظرتان را اینجا بنویسید... (مثلاً: ساخت وب‌سرویس مدیریت فروش و انبارداری با FastAPI و داشبورد وب)"
                  : "Type your project idea or requirements here... (e.g. Build an inventory API with FastAPI and web dashboard)"
              }
              value={autonomousPrompt}
              onChange={(e) => setAutonomousPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                  e.preventDefault();
                  handleLaunchAutonomousForge();
                }
              }}
              rows={3}
            />

            <div className="hero-bar-footer">
              <div className="hero-lead-badge">
                <span>⚡</span>
                <span>{isFa ? "دستیار هوشمند نکسوس‌فورج" : "NexusForge Assistant"}</span>
              </div>
              <button
                type="submit"
                className="hero-launch-button"
                disabled={isLaunchingPrompt || !autonomousPrompt.trim()}
              >
                {isLaunchingPrompt ? (
                  <>
                    <span className="spinner-mini"></span>
                    <span>{isFa ? "در حال شروع..." : "Launching..."}</span>
                  </>
                ) : (
                  <>
                    <span>🚀</span>
                    <span>{isFa ? "شروع پروژه با تیم ۱۲ ایجنتی" : "Launch with 12 Agents"}</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </form>

        {/* Quick Suggestion Chips */}
        <div className="hero-chips-row">
          <span className="chips-label">{isFa ? "ایده‌های آماده برای شروع:" : "Quick Ideas:"}</span>
          <button
            type="button"
            className="chip-item"
            onClick={() => setAutonomousPrompt(isFa ? "یک وب‌سرویس مدیریت انبار و کالا با FastAPI و پنل وب" : "Inventory management API with FastAPI and web dashboard")}
          >
            🛒 {isFa ? "سامانه انبارداری و کالا" : "Inventory Management"}
          </button>
          <button
            type="button"
            className="chip-item"
            onClick={() => setAutonomousPrompt(isFa ? "سیستم مدیریت تسک‌ها، اولویت‌بندی و دسته‌بندی کارها" : "Task management system with priorities and categories")}
          >
            📝 {isFa ? "مدیریت تسک‌ها و کارها" : "Task Management"}
          </button>
          <button
            type="button"
            className="chip-item"
            onClick={() => setAutonomousPrompt(isFa ? "داشبورد تحلیلی و گزارش‌گیری داده‌ها با متدهای RESTful" : "Data analytics dashboard with RESTful endpoints")}
          >
            📊 {isFa ? "داشبورد آمار و تحلیل داده" : "Analytics Dashboard"}
          </button>
        </div>
      </section>

      {/* 3. THREE CLEAN SYSTEM STATUS PILLS */}
      <section className="status-pills-row">
        <div className="status-pill-clean">
          <span className="dot online"></span>
          <span>{isFa ? "سرور آماده و فعال" : "Server Online"}</span>
        </div>
        <div className="status-pill-clean">
          <span className="dot online"></span>
          <span>{isFa ? "۱۲ ایجنت تخصصی آماده" : "12 Specialized Agents Ready"}</span>
        </div>
        <div className="status-pill-clean">
          <span className="dot online"></span>
          <span>{isFa ? "مدل‌های رایگان و بدون محدودیت" : "Free Unlimited Models"}</span>
        </div>
      </section>

      {/* 4. RECENT PROJECTS LIST */}
      <section className="recent-projects-card">
        <div className="projects-card-header">
          <div>
            <h2 className="section-title">{isFa ? "پروژه‌های اخیر شما" : "Recent Projects"}</h2>
            <p className="section-desc">
              {isFa
                ? "برای ورود به محیط استودیو، چت با آریا و مشاهده کدها روی پروژه کلیک کنید."
                : "Click any project to enter the studio, chat with Arya, and inspect deliverables."}
            </p>
          </div>
          <div className="header-actions">
            <button className="btn-secondary-sm" onClick={() => navigate("/projects")}>
              {isFa ? `مشاهده همه (${projects.length})` : `View All (${projects.length})`}
            </button>
          </div>
        </div>

        {loading ? (
          <div className="projects-loading">
            <div className="spinner-mini"></div>
            <span>{isFa ? "در حال بارگذاری پروژه‌ها..." : "Loading projects..."}</span>
          </div>
        ) : projects.length === 0 ? (
          <div className="projects-empty">
            <span className="empty-icon">📂</span>
            <h3>{isFa ? "هنوز پروژه‌ای ثبت نشده است" : "No Projects Yet"}</h3>
            <p>{isFa ? "یک ایده در کادر بالا بنویسید یا دکمه «پروژه جدید» را بزنید." : "Enter a prompt above or click New Project to get started."}</p>
          </div>
        ) : (
          <div className="projects-grid-clean">
            {projects.slice(0, 6).map((proj) => (
              <div
                key={proj.id}
                className="project-tile"
                onClick={() => navigate(`/projects/${proj.id}`)}
              >
                <div className="tile-top">
                  <span className="tile-icon">🚀</span>
                  <div className="tile-info">
                    <h3 className="tile-name">{proj.name}</h3>
                    <p className="tile-desc">{proj.description || (isFa ? "بدون توضیحات" : "No description")}</p>
                  </div>
                  <button
                    className="tile-delete-btn"
                    title={isFa ? "حذف پروژه" : "Delete Project"}
                    onClick={(e) => handleDeleteProject(proj.id, proj.name, e)}
                  >
                    🗑️
                  </button>
                </div>

                <div className="tile-bottom">
                  <span className="tile-ws">
                    📁 {proj.workspace_path ? proj.workspace_path.split("/").pop() || proj.workspace_path : `workspaces/${proj.id.slice(0, 6)}`}
                  </span>
                  <span className="tile-badge">
                    🟢 {isFa ? "آماده در استودیو" : "Ready"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* 5. MODAL FOR NEW PROJECT */}
      {showNewProjectModal && (
        <div className="modal-overlay" onClick={() => setShowNewProjectModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>📁 {isFa ? "تعریف پروژه جدید" : "Create New Project"}</h3>
            <p className="modal-desc">
              {isFa
                ? "نام و توضیحات پروژه را وارد کنید. تیم ۱۲ ایجنتی پروژه را برای شما آماده می‌کند."
                : "Enter project name and details. The 12-agent squad will initialize the environment."}
            </p>

            <form onSubmit={handleCreateProject}>
              <div className="form-group">
                <label>{isFa ? "نام پروژه *" : "Project Name *"}</label>
                <input
                  type="text"
                  className="modal-input"
                  placeholder={isFa ? "مثال: سامانه انبارداری هوشمند" : "e.g. Smart Inventory"}
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  required
                  autoFocus
                />
              </div>

              <div className="form-group">
                <label>{isFa ? "توضیحات و اهداف پروژه:" : "Description & Goals:"}</label>
                <textarea
                  className="modal-input"
                  placeholder={isFa ? "اهداف و ویژگی‌های مورد نظر پروژه را بنویسید..." : "Project requirements..."}
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                  rows={3}
                />
              </div>

              <div className="form-group">
                <label>{isFa ? "مسیر پوشه کاری در رایانه (اختیاری):" : "Workspace Path (Optional):"}</label>
                <input
                  type="text"
                  className="modal-input"
                  placeholder="workspaces/my_project"
                  value={newProjectWorkspacePath}
                  onChange={(e) => setNewProjectWorkspacePath(e.target.value)}
                />
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowNewProjectModal(false)}
                >
                  {isFa ? "انصراف" : "Cancel"}
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={creatingProject || !newProjectName.trim()}
                >
                  {creatingProject ? (isFa ? "در حال ایجاد..." : "Creating...") : (isFa ? "ایجاد و ورود به استودیو" : "Create & Enter Studio")}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;