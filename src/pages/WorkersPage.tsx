import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useLanguage } from "../context/LanguageContext";
import Loading from "../components/Loading";
import "./WorkersPage.css";

interface WorkerNode {
  id: string;
  worker_id: string;
  hostname: string;
  status: "active" | "busy" | "idle" | string;
  current_task_id: string | null;
  current_task_title?: string | null;
  agent_role?: string | null;
  last_heartbeat: string;
  started_at: string;
  tasks_completed: number;
  cpu_usage: number;
  memory_usage: string;
  meta_info?: {
    concurrency?: number;
    engine?: string;
    assigned_agents?: string[];
  };
}

export const WorkersPage: React.FC = () => {
  const { language } = useLanguage();
  const [workers, setWorkers] = useState<WorkerNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "active" | "busy">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  const [queueStats, setQueueStats] = useState<{ queued: number; running: number; completed: number; failed: number } | null>(null);

  const loadWorkers = async () => {
    try {
      const response = await fetch("/api/workers");
      if (response.ok) {
        const data = await response.json();
        setWorkers(data.workers || []);
        if (data.queue_stats) {
          setQueueStats(data.queue_stats);
        }
      }
    } catch (error) {
      console.error("Failed to load workers:", error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadWorkers();
    const interval = setInterval(loadWorkers, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleManualRefresh = () => {
    setRefreshing(true);
    loadWorkers();
  };

  const totalWorkers = workers.length;
  const activeWorkers = workers.filter((w) => w.status === "active").length;
  const busyWorkers = workers.filter((w) => w.status === "busy").length;
  const totalCompleted = queueStats?.completed ?? workers.reduce((acc, w) => acc + (w.tasks_completed || 0), 0);

  const filteredWorkers = workers.filter((w) => {
    if (filter === "active" && w.status !== "active") return false;
    if (filter === "busy" && w.status !== "busy") return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const inId = (w.id || w.worker_id || "").toLowerCase().includes(q);
      const inHost = (w.hostname || w.name || "").toLowerCase().includes(q);
      const inTask = (w.current_task_title || "").toLowerCase().includes(q);
      const inAgent = (w.meta_info?.assigned_agents || []).some((a) => a.toLowerCase().includes(q));
      return inId || inHost || inTask || inAgent;
    }
    return true;
  });

  return (
    <div className="workers-page">
      {/* Header */}
      <header className="workers-page__header">
        <div>
          <div className="workers-page__badge">
            {language === "fa" ? "محیط مانیتورینگ خوشه‌های پردازشی" : "Distributed Worker Execution Pool"}
          </div>
          <h1 className="workers-page__title">
            {language === "fa" ? "وضعیت و پایش نودهای پردازشی" : "Worker Nodes & Telemetry"}
          </h1>
          <p className="workers-page__desc">
            {language === "fa"
              ? "پایش سلامت گره‌های ابری، نظارت بر منابع پردازشی CPU و رم و بررسی اجرای زنده وظایف ایجنت‌های خودمختار."
              : "Live telemetry, resource utilization, and autonomous agent dispatch status across worker nodes."}
          </p>
        </div>

        <div className="workers-page__header-actions">
          <div className="workers-conn-badge">
            <span className="workers-conn-dot" />
            <span>{language === "fa" ? "خوشه متصل و فعال" : "Cluster Online"}</span>
          </div>
          <button
            className="btn btn-outline"
            onClick={handleManualRefresh}
            disabled={refreshing}
            style={{ minWidth: "110px" }}
          >
            {refreshing ? (language === "fa" ? "در حال بروزرسانی..." : "Refreshing...") : (language === "fa" ? "↻ بروزرسانی" : "↻ Refresh")}
          </button>
        </div>
      </header>

      {/* Educational Architecture Explanation Banner */}
      <div className="worker-edu-banner">
        <div className="worker-edu-icon">⚙️</div>
        <div className="worker-edu-content">
          <h3 className="worker-edu-title">
            {language === "fa" ? "ورکر (Worker) چیست و این صفحه چه چیزی را نشان می‌دهد؟" : "What is a Worker and what does this page display?"}
          </h3>
          <p className="worker-edu-text">
            {language === "fa"
              ? "ورکرها موتورهای اجرایی پس‌زمینه (Background Daemons) هستند. تولید معماری نرم‌افزار، فراخوانی مدل‌های هوش مصنوعی، ساخت کد و اجرای اسکریپت‌ها در ترمینال کارهای سنگین و زمان‌بری هستند. وب‌سرور برای اینکه صفحه قفل نشود، تسک‌ها را درون صف قرار می‌دهد. سپس ورکر لوکال این تسک‌ها را برداشته، تیم ایجنت‌ها را بیدار کرده و مستقیماً کدها را در ترمینال ورک‌اسپیس پروژه اجرا می‌کند."
              : "Workers are background daemon processes that continuously poll the task queue. Instead of freezing the web application with heavy AI synthesis and code generation, workers autonomously pick up queued tasks, coordinate agent roles, run terminal verification scripts, and deliver completed project artifacts."}
          </p>
          <div className="worker-edu-pills">
            <div className="edu-pill">
              <span className="edu-pill-bullet">1</span>
              <span>{language === "fa" ? "صف تسک‌ها (Queue): تسک‌های در نوبت اجرا" : "Task Queue: Queued work"}</span>
            </div>
            <div className="edu-pill">
              <span className="edu-pill-bullet">2</span>
              <span>{language === "fa" ? "فراخوانی مدل‌ها و ایجنت‌ها (Arya, Vulcan, Prism)" : "Agent Collaboration"}</span>
            </div>
            <div className="edu-pill">
              <span className="edu-pill-bullet">3</span>
              <span>{language === "fa" ? "دسترسی و اجرای دستور در ترمینال شل" : "Terminal Workspace Runner"}</span>
            </div>
            <div className="edu-pill">
              <span className="edu-pill-bullet">4</span>
              <span>{language === "fa" ? "تولید مستندات، فایل‌های کد و گزارش سلامت" : "Deliverables & PRD Synthesis"}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="workers-stats-grid">
        <div className="worker-stat-card">
          <span className="worker-stat-val">{totalWorkers}</span>
          <span className="worker-stat-label">
            {language === "fa" ? "کل گره‌های فعال" : "Total Nodes"}
          </span>
        </div>
        <div className="worker-stat-card">
          <span className="worker-stat-val" style={{ color: "#34D399" }}>{activeWorkers}</span>
          <span className="worker-stat-label">
            {language === "fa" ? "گره‌های آماده‌به‌کار" : "Ready / Idle"}
          </span>
        </div>
        <div className="worker-stat-card">
          <span className="worker-stat-val" style={{ color: "#FACC15" }}>{busyWorkers}</span>
          <span className="worker-stat-label">
            {language === "fa" ? "در حال پردازش تسک" : "Actively Executing"}
          </span>
        </div>
        <div className="worker-stat-card">
          <span className="worker-stat-val" style={{ color: "#38BDF8" }}>{totalCompleted}</span>
          <span className="worker-stat-label">
            {language === "fa" ? "تسک‌های تکمیل شده" : "Tasks Delivered"}
          </span>
        </div>
      </div>

      {/* Toolbar */}
      <div className="workers-toolbar">
        <input
          type="text"
          className="workers-search"
          placeholder={language === "fa" ? "جستجوی گره، هاست یا ایجنت تخصیص یافته..." : "Search node, hostname, or assigned agent..."}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />

        <div className="workers-tabs">
          <button
            className={`worker-tab ${filter === "all" ? "active" : ""}`}
            onClick={() => setFilter("all")}
          >
            {language === "fa" ? "همه" : "All"} ({workers.length})
          </button>
          <button
            className={`worker-tab ${filter === "active" ? "active" : ""}`}
            onClick={() => setFilter("active")}
          >
            {language === "fa" ? "آماده" : "Ready"} ({activeWorkers})
          </button>
          <button
            className={`worker-tab ${filter === "busy" ? "active" : ""}`}
            onClick={() => setFilter("busy")}
          >
            {language === "fa" ? "مشغول" : "Busy"} ({busyWorkers})
          </button>
        </div>
      </div>

      {/* Grid */}
      {loading ? (
        <Loading message={language === "fa" ? "در حال استعلام تله‌متری گره‌ها..." : "Loading worker node telemetry..."} />
      ) : (
        <div className="workers-grid">
          {filteredWorkers.map((worker) => {
            const displayId = worker.id || worker.worker_id || "worker-node";
            const displayHost = worker.hostname || worker.name || "Worker Node";
            return (
            <div key={displayId} className="worker-node-card">
              <div className="worker-card__top">
                <div className="worker-card__identity">
                  <div className="worker-icon-box">🖥️</div>
                  <div>
                    <h3 className="worker-hostname">{displayHost}</h3>
                    <span className="worker-id-tag">ID: {displayId}</span>
                  </div>
                </div>
                <span className={`worker-status-badge worker-status-badge--${worker.status}`}>
                  {worker.status === "active"
                    ? (language === "fa" ? "آماده" : "Active")
                    : worker.status === "busy"
                    ? (language === "fa" ? "در حال اجرا" : "Busy")
                    : worker.status}
                </span>
              </div>

              {/* Active task section */}
              {worker.current_task_title ? (
                <div className="worker-task-box">
                  <div className="worker-task-label">
                    {language === "fa" ? "تسک فعال تحت هدایت:" : "Active Execution Target:"}
                  </div>
                  <div className="worker-task-title">
                    ⚡ {worker.current_task_title}
                  </div>
                </div>
              ) : (
                <div className="worker-task-box" style={{ opacity: 0.65 }}>
                  <div className="worker-task-label">
                    {language === "fa" ? "وضعیت تسک:" : "Task Status:"}
                  </div>
                  <div className="worker-task-title" style={{ fontSize: "0.85rem", color: "#94A3B8" }}>
                    {language === "fa" ? "در انتظار دریافت تسک جدید از آریا" : "Idle — waiting for dispatch from Arya"}
                  </div>
                </div>
              )}

              {/* Telemetry metrics */}
              <div className="worker-telemetry">
                <div className="telemetry-item">
                  <span className="telemetry-label">{language === "fa" ? "بار پردازنده" : "CPU Load"}</span>
                  <span className="telemetry-val">{worker.cpu_usage}%</span>
                  <div className="progress-bar-wrap">
                    <div
                      className="progress-bar-fill"
                      style={{ width: `${Math.min(100, worker.cpu_usage * 2.5)}%` }}
                    />
                  </div>
                </div>
                <div className="telemetry-item">
                  <span className="telemetry-label">{language === "fa" ? "مصرف رم" : "Memory"}</span>
                  <span className="telemetry-val">{worker.memory_usage}</span>
                  <span style={{ fontSize: "0.75rem", color: "#64748B", marginTop: "4px" }}>
                    {language === "fa" ? "تسک‌های تمام شده: " : "Tasks: "} {worker.tasks_completed}
                  </span>
                </div>
              </div>

              {/* Assigned squad */}
              {worker.meta_info?.assigned_agents && (
                <div>
                  <div style={{ fontSize: "0.72rem", color: "#94A3B8", marginBottom: "6px", fontWeight: 600, textTransform: "uppercase" }}>
                    {language === "fa" ? "ایجنت‌های مستقر روی این گره:" : "Assigned Agent Squad:"}
                  </div>
                  <div className="worker-squad-wrap">
                    {worker.meta_info.assigned_agents.map((agentName, idx) => (
                      <span key={idx} className="squad-chip">
                        ✦ {agentName}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
            );
          })}

          {filteredWorkers.length === 0 && (
            <div className="empty-workers-box">
              <h3 style={{ color: "#FFFFFF", marginBottom: "8px" }}>
                {language === "fa" ? "گره‌ای با این مشخصات یافت نشد" : "No Worker Nodes Found"}
              </h3>
              <p style={{ color: "#94A3B8" }}>
                {language === "fa" ? "فیلتر جستجو را پاک کنید یا گره‌های جدید را راه‌اندازی کنید." : "Try clearing your search query or check cluster connectivity."}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default WorkersPage;
