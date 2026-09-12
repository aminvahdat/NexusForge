import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Worker } from "../types";
import { api } from "../services/api";
import { Skeleton } from "../components/Skeleton";
import { Toast } from "../components/Toast";
import "./Workers.css";

/* Workers monitoring page — real-time worker health and metrics */
export const WorkersPage: React.FC = () => {
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [toast, setToast] = useState<{
    type: "success" | "error" | "info";
    title: string;
    message: string;
  } | null>(null);

  // Load workers
  useEffect(() => {
    loadWorkers();
  }, []);

  const loadWorkers = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/workers");
      if (response.ok) {
        const data = await response.json();
        setWorkers(data.workers || []);
      } else {
        // Fallback: show cached or empty state
        setWorkers([]);
      }
    } catch (error) {
      console.error("Failed to load workers:", error);
    } finally {
      setLoading(false);
    }
  };

  // WebSocket for real-time worker updates
  useEffect(() => {
    const clientId = "workers-" + Date.now();
    const ws = new WebSocket(
      `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/execution/ws/${clientId}`
    );

    ws.onopen = () => setWsConnected(true);
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === "worker_heartbeat" && message.data) {
          setWorkers((prev) => {
            const updated = message.data as Worker;
            const existing = prev.find((w) => w.id === updated.id);
            if (existing) {
              return prev.map((w) => (w.id === updated.id ? { ...w, ...updated } : w));
            }
            return [...prev, updated];
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

  const totalWorkers = workers.length;
  const activeWorkers = workers.filter((w) => w.status === "active").length;
  const busyWorkers = workers.filter((w) => w.status === "busy").length;

  return (
    <div className="workers">
      <header className="workers__header">
        <h1 className="workers__title">Worker Monitoring</h1>
        <div className="workers__connection">
          <span
            className={`workers__status-dot ${wsConnected ? "workers__status-dot--connected" : "workers__status-dot--disconnected"}`}
            aria-hidden="true"
          />
          <span className="workers__status-text">
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

      {/* Worker stats */}
      <section className="workers__stats" aria-label="Worker statistics">
        <div className="workers__stat-card">
          <h3 className="workers__stat-value">{totalWorkers}</h3>
          <p className="workers__stat-label">Total Workers</p>
        </div>
        <div className="workers__stat-card">
          <h3 className="workers__stat-value">{activeWorkers}</h3>
          <p className="workers__stat-label">Active</p>
        </div>
        <div className="workers__stat-card">
          <h3 className="workers__stat-value">{busyWorkers}</h3>
          <p className="workers__stat-label">Busy</p>
        </div>
      </section>

      {/* Workers list */}
      <section className="workers__list" aria-label="Worker list">
        <h2 className="workers__section-title">Workers</h2>
        {loading ? (
          <Skeleton width="100%" height="200px" />
        ) : workers.length === 0 ? (
          <div className="empty-state">
            <h3 className="empty-state__title">No Workers Connected</h3>
            <p className="empty-state__description">
              Workers will appear here once they connect to the system.
            </p>
            <Link to="/" className="btn btn-primary btn-sm">
              View Dashboard
            </Link>
          </div>
        ) : (
          <div className="workers__grid">
            {workers.map((worker) => (
              <Link
                key={worker.id}
                to={`/workers/${worker.id}`}
                className={`workers__card ${worker.status === "active" ? "workers__card--active" : ""}`}
                aria-label={`Worker ${worker.id}: ${worker.status}`}
              >
                <div className="workers__card-header">
                  <span className="workers__card-name">{worker.id}</span>
                  <span
                    className={`workers__card-status workers__card-status--${worker.status}`}
                  >
                    {worker.status}
                  </span>
                </div>
                <div className="workers__card-body">
                  <div className="workers__card-metric">
                    <span className="workers__card-label">Tasks Done</span>
                    <span className="workers__card-value">{worker.tasks_completed}</span>
                  </div>
                  <div className="workers__card-metric">
                    <span className="workers__card-label">CPU Usage</span>
                    <span className="workers__card-value">{worker.cpu_usage}%</span>
                  </div>
                  <div className="workers__card-metric">
                    <span className="workers__card-label">Memory</span>
                    <span className="workers__card-value">{worker.memory_usage}</span>
                  </div>
                  <div className="workers__card-metric">
                    <span className="workers__card-label">Last Heartbeat</span>
                    <span className="workers__card-value">
                      {worker.last_heartbeat
                        ? new Date(worker.last_heartbeat).toLocaleTimeString()
                        : "N/A"}
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
export default WorkersPage;
