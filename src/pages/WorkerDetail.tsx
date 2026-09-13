import React, { useState, useEffect } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { Worker } from "../types";
import { Skeleton } from "../components/Skeleton";
import { Loading } from "../components/Loading";
import { EmptyState } from "../components/EmptyState";
import { api } from "../services/api";

export const WorkerDetail: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [worker, setWorker] = useState<any>(null);
  const [isLoading, setLoading] = useState(true);

  useEffect(() => {
    async function loadWorker() {
      try {
        const response = await api.workers.getById(id);
        setWorker(response.data);
        setLoading(false);
      } catch (error) {
        console.error("Failed to load worker:", error);
        setLoading(false);
      }
    };

    loadWorker();
  }, [id]);

  if (isLoading) {
    return (
      <div className="worker-detail">
        <div className="worker-detail__loading">
          <Skeleton />
          <p>Loading worker information...</p>
        </div>
      </div>
    );
  }

  if (!worker) {
    return (
      <div className="worker-detail">
        <div className="worker-detail__empty">
          <EmptyState title="Worker Not Found" description="Could not find the requested worker." />
        </div>
      </div>
    );
  }

  const handlePause = async () => {
    if (!worker) return;
    try {
      await api.workers.pause(worker.worker_id);
      setWorker((prev: any) => prev ? { ...prev, status: "paused" } : prev);
    } catch (err) {
      console.error("Failed to pause worker:", err);
    }
  };

  const handleResume = async () => {
    if (!worker) return;
    try {
      await api.workers.resume(worker.worker_id);
      setWorker((prev: any) => prev ? { ...prev, status: "active" } : prev);
    } catch (err) {
      console.error("Failed to resume worker:", err);
    }
  };

  const handleRetire = async () => {
    if (!worker) return;
    try {
      await api.workers.retire(worker.worker_id);
      setWorker((prev: any) => prev ? { ...prev, status: "retired" } : prev);
    } catch (err) {
      console.error("Failed to retire worker:", err);
    }
  };

  return (
    <div className="worker-detail">
      <div className="worker-detail-header">
        <h1>Worker {worker.worker_id}</h1>
        <Link to="/workers" className="back-button">
          ← Workers
        </Link>
      </div>

      <div className="worker-detail__content">
        <div className="worker-detail-header">
          <h2>Worker {worker.worker_id}</h2>
          <div className={`worker-status-badge ${worker.status?.toLowerCase() || ''}`}>
            {worker.status}
          </div>
        </div>

        <div className="worker-detail__card">
          <h3>Current Status</h3>
          <p><strong>Status:</strong> {worker.status}</p>
        </div>

        <div className="worker-detail__card">
          <h3>Current Task</h3>
          {worker.tasks && worker.tasks.length > 0 ? (
            worker.tasks.map((task: any) => (
              <div key={task.id} className="task-item">
                <h4>{task.title}</h4>
                <p><strong>Status:</strong> {task.status}</p>
                <span className={`task-badge ${task.status?.toLowerCase() || ''}`}>{task.status}</span>
              </div>
            ))
          ) : (
            <div className="task-empty">
              <EmptyState
                title="No tasks assigned"
                description="This worker has no active tasks."
              />
            </div>
          )}
        </div>

        <div className="worker-detail__card">
          <h3>Control Panel</h3>
          <div className="worker-controls">
            {worker.status === "paused" ? (
              <button className="btn btn-primary" onClick={handleResume}>Resume Worker</button>
            ) : (
              <button className="btn btn-secondary" onClick={handlePause}>Pause Worker</button>
            )}
            <button className="btn btn-danger" onClick={handleRetire}>Retire Worker</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkerDetail;
