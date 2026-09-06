import React, { useState, useEffect } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { Worker, ExecutionEvent } from "../types";
import { api } from "../services/api";
import { Skeleton } from "../components/Skeleton";
import { Toast } from "../components/Toast";
import { ExecutionTimeline } from "../components/ExecutionTimeline";
import "./WorkerDetail.css";

/* Worker detail page — individual worker health, metrics, and execution history */
export const WorkerDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [worker, setWorker] = useState<Worker | null>(null);
  const [events, setEvents] = useState<ExecutionEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [toast, setToast] = useState<{
    type: "success" | "error" | "info";
    title: string;
    message: string;
  } | null>(null);

  // Load worker data
  useEffect(() => {
    if (!id) return;

    const loadWorker = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/workers/${id}`);
        if (response.ok) {
          const data = await response.json();
          setWorker(data);
        } else {
          setToast({
            type: "error",
            title: "Worker Not Found",
            message: `Worker ${id} could not be found.`,
          });
          setTimeout(() => navigate("/workers"), 3000);
        }
      } catch (error) {
        console.error("Failed to load worker:", error);
        setToast({
          type: "error",
          title: "Load Error",
          message: "Failed to load worker details. Please try again.",
        });
      } finally {
        setLoading(false);
      }
    };

    loadWorker();
  }, [id, navigate]);

  // WebSocket for real-time worker updates
  useEffect(() => {
    if (!id) return;

    const clientId = "worker-detail-" + Date.now();
    const ws = new WebSocket(
      `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/execution/ws/${clientId}`
    );

    ws.onopen = () => setWsConnected(true);
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === "worker_heartbeat" && message.data) {
          const updated = message.data as Worker;
          if (updated.id === id) {
            setWorker(updated);
          }
        } else if (message.type === "execution_event" && message.data) {
          const newEvent = message.data as ExecutionEvent;
          if (newEvent.worker_id === id) {
            setEvents((prev) => {
              const exists = prev.some(
                (e) =>
                  e.event_type === newEvent.event_type &&
                  e.timestamp === newEvent.timestamp
              );
              if (exists) return prev;
              return [newEvent, ...prev].slice(0, 50);
            });
          }
        }
      } catch {
        // Ignore parse errors
      }
    };
    ws.onerror = () => setWsConnected(false);
    ws.onclose = () => setWsConnected(false);
    return () => ws.close();
  }, [id]);

  if (loading) {
    return (
      <div className="worker-detail">
        <Skeleton width="100%" height="200px" />
        <Skeleton width="100%" height="150px" />
      </div>
    );
  }

  if (!worker) {
    return (
      <div className="worker-detail">
        <div className="empty-state">
          <h3 className="empty-state__title">Worker Not Found</h3>
          <p className="empty-state__description">
            The requested worker could not be found.
          </p>
          <Link to="/workers" className="btn btn-primary btn-sm">
            Back to Workers
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="worker-detail">
      <header className="worker-detail__header">
        <div>
          <Link to="/workers" className="worker-detail__back">
            ← Back to Workers
          </Link>
          <h1 className="worker-detail__title">Worker {worker.id}</h1>
        </div>
        <div className="worker-detail__connection">
          <span
            className={`worker-detail__status-dot ${wsConnected ? "worker-detail__status-dot--connected" : "worker-detail__status-dot--disconnected"}`}
            aria-hidden="true"
          />
          <span className="worker-detail__status-text">
            {wsConnected ? "Live" : "Reconnecting"}
          </span>
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

      {/* Worker status card */}
      <section className="worker-detail__status-card" aria-label="Worker status">
        <div className="worker-detail__status-row">
          <span className="worker-detail__status-label">Status:</span>
          <span
            className={`worker-detail__status-badge worker-detail__status-badge--${worker.status}`}
          >
            {worker.status}
          </span>
        </div>
        <div className="worker-detail__metrics">
          <div className="worker-detail__metric">
            <span className="worker-detail__metric-label">Tasks Completed</span>
            <span className="worker-detail__metric-value">{worker.tasks_completed}</span>
          </div>
          <div className="worker-detail__metric">
            <span className="worker-detail__metric-label">CPU Usage</span>
            <span className="worker-detail__metric-value">{worker.cpu_usage}%</span>
          </div>
          <div className="worker-detail__metric">
            <span className="worker-detail__metric-label">Memory Usage</span>
            <span className="worker-detail__metric-value">{worker.memory_usage}</span>
          </div>
          <div className="worker-detail__metric">
            <span className="worker-detail__metric-label">Last Heartbeat</span>
            <span className="worker-detail__metric-value">
              {worker.last_heartbeat
                ? new Date(worker.last_heartbeat).toLocaleTimeString()
                : "N/A"}
            </span>
          </div>
        </div>
      </section>

      {/* Execution history */}
      <section className="worker-detail__events" aria-label="Execution history">
        <h2 className="worker-detail__section-title">Execution History</h2>
        {events.length === 0 ? (
          <div className="empty-state">
            <h3 className="empty-state__title">No Executions</h3>
            <p className="empty-state__description">
              No execution events have been recorded for this worker yet.
            </p>
          </div>
        ) : (
          <ExecutionTimeline events={events} />
        )}
      </section>
    </div>
  );
};