import React from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { Worker } from "../types";
import { Skeleton } from "./Skeleton";
import { Loading } from "./Loading";
import { EmptyState } from "./EmptyState";

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

    if (!worker) {
      return (
        <div className="worker-detail">
          <div className="worker-detail__empty">
            <EmptyState title="Worker Not Found" description="Could not find the requested worker." />
          </div>
        </div>
      );

    return (
      <div className="worker-detail">
        <div className="worker-detail-header">
          <h1>Worker {worker.worker_id}</h1>
          <Link to="/workers" className="back-button">
            ← Workers
          </Link>
        </div>

        <div className="worker-detail__content">
          <div className="worker-detail__header">
            <h2>Worker {worker.worker_id}</h1>
            <div className="worker-status-badge {worker.status.toLowerCase()}">
              {worker.status}
            </div>
          </div>

          <div className="worker-detail__card">
            <h3>Current Status</h3>
            <p><strong>Status:</strong> {worker.status}</span>
          </div>

          <div className="worker-detail__card">
            <h3>Current Task</h3>
            {tasks.length > 0 ? (
              tasks.map((task) => (
                <div key={task.id} className="task-item">
                  <h4>{task.title}</h4>
                  <p><strong>Status:</strong> {task.status}</span>
                  <span className="task-badge {task.status.toLowerCase()}">{task.status}</span>
                </div>
              </div>
            ) : (
              <div className="task-empty">
                <EmptyState
                  title="No tasks assigned"
                  description="This worker has no active tasks. Click 'Start' to begin a new task."
                />
              </div>
            )}
          </div>

          <div className="worker-detail__card">
            <h3>Execution Timeline</h3>
            <ExecutionTimeline events={worker.execution_events || []} isLoading={isLoading} isLoading={isLoading} />
          </div>

          <div className="worker-detail__card">
            <h3>Control Panel</h3>
            <div className="worker-controls">
              <button className="btn btn-primary" onClick={() => alert('Start execution (mock)')}>Start Execution</button>
              <button className="btn btn-secondary" onClick={() => alert('Pause execution (mock)')}>Pause Execution</button>
              <button className="btn btn-danger" onClick={() => alert('Retire worker (mock)')}>Retire Worker</button>
            </div>
          )}
        </div>
      </div>
    );