import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Project, Task, ExecutionEvent, WebSocketMessage } from "../types";
import { executionApi, projectApi, taskApi } from "../services/api";
import ProjectList from "../components/ProjectList";
import TaskList from "../components/TaskList";
import { ExecutionStatus } from "../components/ExecutionStatus";
import { ExecutionTimeline } from "../components/ExecutionTimeline";
import { Skeleton } from "../components/Skeleton";
import { Toast } from "../components/Toast";
import { EmptyState } from "../components/EmptyState";
import "./Activity.css";

/* Activity overview page — combines task execution, project stats, and real-time monitoring */
export const ActivityPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [events, setEvents] = useState<ExecutionEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [toast, setToast] = useState<{
    type: "success" | "error" | "info";
    title: string;
    message: string;
  } | null>(null);

  // Load initial data
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const projectsRes = await projectApi.getAll();
      const tasksRes = await taskApi.getAll();
      setProjects(projectsRes.data || []);
      setTasks(tasksRes.data || []);

      // Load execution events
      const execRes = await executionApi.list();
      setEvents(execRes.data || []);
    } catch (error) {
      console.error("Failed to load activity data:", error);
      setToast({
        type: "error",
        title: "Load Error",
        message: "Failed to load activity data. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  // Connect WebSocket for real-time updates
  useEffect(() => {
    const clientId = "activity-" + Date.now();
    const ws = new WebSocket(
      `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/execution/ws/${clientId}`
    );

    ws.onopen = () => {
      setWsConnected(true);
      setToast({ type: "info", title: "Connected", message: "Real-time updates enabled." });
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        if (message.type === "execution_event" && message.data) {
          setEvents((prev) => {
            const newEvent = message.data as ExecutionEvent;
            // Deduplicate by timestamp + event_type + worker_id
            const exists = prev.some(
              (e) =>
                e.event_type === newEvent.event_type &&
                e.timestamp === newEvent.timestamp &&
                e.worker_id === newEvent.worker_id
            );
            if (exists) return prev;
            return [newEvent, ...prev].slice(0, 100); // Keep last 100 events
          });
        } else if (message.type === "task_update" && message.data) {
          setTasks((prev) => {
            const updated = message.data as Task;
            return prev.map((t) => (t.id === updated.id ? updated : t));
          });
        } else if (message.type === "execution_complete" || message.type === "execution_failed") {
          setToast({
            type: message.type === "execution_complete" ? "success" : "error",
            title: message.type === "execution_complete" ? "Execution Complete" : "Execution Failed",
            message: `Execution ${message.type === "execution_complete" ? "completed successfully" : "failed"}.`,
          });
          loadData(); // Refresh data after completion
        }
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    };

    ws.onerror = () => {
      setWsConnected(false);
    };

    ws.onclose = () => {
      setWsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, []);

  const projectCount = projects.length;
  const taskCount = tasks.length;
  const activeExecutions = events.filter((e) => {
    const status = e.execution_status;
    return status === "pending" || status === "queued" || status === "assigned" || status === "running";
  }).length;
  const completedExecutions = events.filter((e) => e.event_type === "EXECUTION_COMPLETED").length;
  const failedExecutions = events.filter((e) => e.event_type === "EXECUTION_FAILED").length;

  return (
    <div className="activity">
      <header className="activity__header">
        <h1 className="activity__title">Activity</h1>
        <ExecutionStatus
          status={activeExecutions > 0 ? "running" : "completed"}
          isLive={true}
          connected={wsConnected}
          onRefresh={loadData}
        />
      </header>

      {/* Toast notification */}
      {toast && (
        <Toast
          type={toast.type}
          title={toast.title}
          message={toast.message}
          onClose={() => setToast(null)}
        />
      )}

      {/* Stats cards */}
      <section className="activity__stats" aria-label="Activity statistics">
        <div className="activity__stat-card">
          <h3 className="activity__stat-value">{projectCount}</h3>
          <p className="activity__stat-label">Projects</p>
        </div>
        <div className="activity__stat-card">
          <h3 className="activity__stat-value">{taskCount}</h3>
          <p className="activity__stat-label">Tasks</p>
        </div>
        <div className="activity__stat-card">
          <h3 className="activity__stat-value">{activeExecutions}</h3>
          <p className="activity__stat-label">Active Executions</p>
        </div>
        <div className="activity__stat-card">
          <h3 className="activity__stat-value">{completedExecutions}</h3>
          <p className="activity__stat-label">Completed</p>
        </div>
        <div className="activity__stat-card">
          <h3 className="activity__stat-value">{failedExecutions}</h3>
          <p className="activity__stat-label">Failed</p>
        </div>
      </section>

      {/* Execution timeline */}
      <section className="activity__timeline" aria-label="Execution timeline">
        <h2 className="activity__section-title">Execution Timeline</h2>
        {loading ? (
          <Skeleton width="100%" height="200px" />
        ) : events.length === 0 ? (
          <EmptyState
            title="No Executions Yet"
            description="Start a task execution to see real-time activity here."
            action={{ label: "Create a Task", to: "/projects" }}
          />
        ) : (
          <ExecutionTimeline events={events} />
        )}
      </section>

      {/* Recent tasks */}
      <section className="activity__tasks" aria-label="Recent tasks">
        <h2 className="activity__section-title">Recent Tasks</h2>
        {loading ? (
          <Skeleton width="100%" height="150px" />
        ) : tasks.length === 0 ? (
          <EmptyState
            title="No Tasks"
            description="Create tasks from your projects to track execution activity."
            action={{ label: "View Projects", to: "/projects" }}
          />
        ) : (
          <TaskList tasks={tasks} />
        )}
      </section>

      {/* Recent projects */}
      <section className="activity__projects" aria-label="Recent projects">
        <h2 className="activity__section-title">Projects</h2>
        {loading ? (
          <Skeleton width="100%" height="100px" />
        ) : projects.length === 0 ? (
          <EmptyState
            title="No Projects"
            description="Create a project to organize your tasks and track execution activity."
            action={{ label: "Create Project", to: "/projects" }}
          />
        ) : (
          <ProjectList projects={projects} />
        )}
      </section>
    </div>
  );
};

export default ActivityPage;
