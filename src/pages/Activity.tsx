import React, { useState, useEffect } from "react";
import { useLanguage } from "../context/LanguageContext";
import { Project, Task, ExecutionEvent } from "../types";
import { executionApi, projectApi, taskApi } from "../services/api";
import Loading from "../components/Loading";
import "./Activity.css";

export const ActivityPage: React.FC = () => {
  const { language } = useLanguage();
  const [projects, setProjects] = useState<Project[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [events, setEvents] = useState<ExecutionEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "running" | "completed" | "failed">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    try {
      const [projectsRes, tasksRes, execRes] = await Promise.all([
        projectApi.getAll().catch(() => []),
        taskApi.getAll().catch(() => []),
        executionApi.list().catch(() => []),
      ]);

      setProjects(Array.isArray(projectsRes) ? projectsRes : []);
      setTasks(Array.isArray(tasksRes) ? tasksRes : []);
      setEvents(Array.isArray(execRes) ? execRes : []);
    } catch (error) {
      console.error("Failed to load activity data:", error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleManualRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const projectCount = projects.length;
  const taskCount = tasks.length;
  const activeExecutions = events.filter((e) => {
    const s = (e.execution_status || "").toLowerCase();
    return s === "running" || s === "queued" || s === "assigned" || e.event_type === "EXECUTION_STARTED";
  }).length;
  const completedExecutions = events.filter((e) => e.event_type === "EXECUTION_COMPLETED" || e.execution_status === "completed").length;
  const failedExecutions = events.filter((e) => e.event_type === "EXECUTION_FAILED" || e.execution_status === "failed").length;

  const filteredEvents = events.filter((e) => {
    const s = (e.execution_status || "").toLowerCase();
    const t = (e.event_type || "").toLowerCase();
    if (filter === "running" && !(s === "running" || s === "queued" || t.includes("start"))) return false;
    if (filter === "completed" && !(s === "completed" || t.includes("complet"))) return false;
    if (filter === "failed" && !(s === "failed" || t.includes("fail"))) return false;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const inType = t.includes(q);
      const inWorker = (e.worker_id || "").toLowerCase().includes(q);
      const inTask = (e.task_id || "").toLowerCase().includes(q);
      const inData = JSON.stringify(e.data || {}).toLowerCase().includes(q);
      return inType || inWorker || inTask || inData;
    }
    return true;
  });

  const getBadgeClass = (eventType: string, status?: string) => {
    const s = (status || "").toLowerCase();
    const t = (eventType || "").toLowerCase();
    if (s === "running" || t.includes("start")) return "event-type--started";
    if (s === "completed" || t.includes("complet")) return "event-type--completed";
    if (s === "failed" || t.includes("fail")) return "event-type--failed";
    return "event-type--default";
  };

  return (
    <div className="activity-page">
      {/* Header */}
      <header className="activity-page__header">
        <div>
          <div className="activity-page__badge">
            {language === "fa" ? "مانیتورینگ بلادرنگ رخدادها" : "Real-Time Event Stream"}
          </div>
          <h1 className="activity-page__title">
            {language === "fa" ? "لاگ‌ها و رویدادهای زنده سیستم" : "Live Execution Activity"}
          </h1>
          <p className="activity-page__desc">
            {language === "fa"
              ? "مشاهده زنده رویدادهای اجرای تسک‌ها، استقرار ایجنت‌ها، تغییر وضعیت پروژه‌ها و گزارش خروجی‌ها."
              : "Monitor execution lifecycles, worker assignments, milestone completions, and error telemetry in real time."}
          </p>
        </div>

        <div className="activity-page__header-actions">
          <div className="stream-status-badge">
            <span className="stream-status-dot" />
            <span>{language === "fa" ? "جریان داده زنده" : "Live Stream Active"}</span>
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

      {/* Stats Cards */}
      <div className="activity-stats-grid">
        <div className="activity-stat-card">
          <span className="activity-stat-val">{projectCount}</span>
          <span className="activity-stat-label">
            {language === "fa" ? "کل پروژه‌ها" : "Total Projects"}
          </span>
        </div>
        <div className="activity-stat-card">
          <span className="activity-stat-val" style={{ color: "#38BDF8" }}>{taskCount}</span>
          <span className="activity-stat-label">
            {language === "fa" ? "کل تسک‌ها" : "Total Tasks"}
          </span>
        </div>
        <div className="activity-stat-card">
          <span className="activity-stat-val" style={{ color: "#FACC15" }}>{activeExecutions}</span>
          <span className="activity-stat-label">
            {language === "fa" ? "در حال اجرا" : "Active Runs"}
          </span>
        </div>
        <div className="activity-stat-card">
          <span className="activity-stat-val" style={{ color: "#34D399" }}>{completedExecutions}</span>
          <span className="activity-stat-label">
            {language === "fa" ? "موفق" : "Completed"}
          </span>
        </div>
        <div className="activity-stat-card">
          <span className="activity-stat-val" style={{ color: "#F87171" }}>{failedExecutions}</span>
          <span className="activity-stat-label">
            {language === "fa" ? "ناموفق" : "Failed"}
          </span>
        </div>
      </div>

      {/* Toolbar */}
      <div className="activity-toolbar">
        <input
          type="text"
          className="activity-search"
          placeholder={language === "fa" ? "جستجوی رخداد، شناسه ورکر یا تسک..." : "Search event type, worker ID, or task..."}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />

        <div className="activity-tabs">
          <button
            className={`activity-tab ${filter === "all" ? "active" : ""}`}
            onClick={() => setFilter("all")}
          >
            {language === "fa" ? "همه" : "All"} ({events.length})
          </button>
          <button
            className={`activity-tab ${filter === "running" ? "active" : ""}`}
            onClick={() => setFilter("running")}
          >
            {language === "fa" ? "در حال اجرا" : "Running"} ({activeExecutions})
          </button>
          <button
            className={`activity-tab ${filter === "completed" ? "active" : ""}`}
            onClick={() => setFilter("completed")}
          >
            {language === "fa" ? "تکمیل شده" : "Completed"} ({completedExecutions})
          </button>
          <button
            className={`activity-tab ${filter === "failed" ? "active" : ""}`}
            onClick={() => setFilter("failed")}
          >
            {language === "fa" ? "ناموفق" : "Failed"} ({failedExecutions})
          </button>
        </div>
      </div>

      {/* Live Event Feed */}
      {loading ? (
        <Loading message={language === "fa" ? "در حال بارگذاری جریان رویدادها..." : "Loading live activity stream..."} />
      ) : (
        <div className="activity-feed">
          {filteredEvents.map((evt, idx) => {
            const badgeClass = getBadgeClass(evt.event_type, evt.execution_status);
            const displayTitle = evt.event_type.replace(/_/g, " ");
            const timeStr = evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : "Just now";

            return (
              <div key={idx} className="event-card">
                <div className="event-card__left">
                  <span className={`event-type-badge ${badgeClass}`}>
                    {evt.execution_status || evt.event_type}
                  </span>
                  <div className="event-summary">
                    <span className="event-title">{displayTitle}</span>
                    <span className="event-subtitle">
                      {evt.task_id ? `Task: ${evt.task_id}` : `Worker: ${evt.worker_id || "System"}`}
                    </span>
                  </div>
                </div>

                <div className="event-card__right">
                  {evt.worker_id && (
                    <span className="event-worker-chip">
                      🖥️ {evt.worker_id}
                    </span>
                  )}
                  <span className="event-time">
                    ⏱ {timeStr}
                  </span>
                </div>
              </div>
            );
          })}

          {filteredEvents.length === 0 && (
            <div className="empty-events-box">
              <h3 style={{ color: "#FFFFFF", marginBottom: "8px" }}>
                {language === "fa" ? "رویدادی با این مشخصات یافت نشد" : "No Execution Events Found"}
              </h3>
              <p style={{ color: "#94A3B8" }}>
                {language === "fa" ? "فیلتر جستجو را پاک کنید یا تسک جدیدی را اجرا کنید." : "Try modifying your filter or launch a new autonomous project."}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ActivityPage;
