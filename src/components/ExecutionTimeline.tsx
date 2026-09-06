import React from "react";
import { ExecutionEvent } from "../types";
import { Skeleton } from "./Skeleton";

interface ExecutionTimelineProps {
  events: ExecutionEvent[];
  isLoading?: boolean;
}

export const ExecutionTimeline: React.FC<ExecutionTimelineProps> = ({
  events,
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <div className="execution-timeline" aria-busy="true">
        <SkeletonTimeline />
      </div>
    );
  }

  if (!events || events.length === 0) {
    return (
      <div className="execution-timeline execution-timeline--empty">
        <div className="empty-state" role="status" aria-label="No execution events yet">
          <svg
            className="empty-state__icon"
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          <h3 className="empty-state__title">No Events Yet</h3>
          <p className="empty-state__description">
            Execution events will appear here as the task progresses.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      className="execution-timeline"
      role="region"
      aria-label="Execution event timeline"
    >
      {events.map((event, index) => (
        <article
          key={`${event.event_type}-${index}`}
          className="execution-timeline__item"
          aria-label={`${event.event_type} at ${new Date(event.timestamp).toLocaleTimeString()}`}
        >
          <div
            className="execution-timeline__dot"
            style={{
              background:
                event.event_type === "EXECUTION_COMPLETED"
                  ? "#10b981"
                  : event.event_type === "EXECUTION_FAILED"
                  ? "#ef4444"
                  : "#7C3AED",
            }}
            aria-hidden="true"
          />
          <div className="execution-timeline__content">
            <div className="execution-timeline__header">
              <span className="execution-timeline__type" aria-label="Event type">
                {event.event_type}
              </span>
              <time
                className="execution-timeline__time"
                dateTime={new Date(event.timestamp).toISOString()}
                aria-label="Event timestamp"
              >
                {new Date(event.timestamp).toLocaleTimeString()}
              </time>
            </div>
            <p className="execution-timeline__message">{event.message}</p>
            {event.worker_id && (
              <span
                className="execution-timeline__worker"
                aria-label={`Assigned to worker ${event.worker_id}`}
              >
                Worker: {event.worker_id}
              </span>
            )}
            {event.metadata?.progress && (
              <div
                className="execution-timeline__progress"
                aria-label={`Progress: ${(event.metadata.progress * 100).toFixed(0)}%`}
              >
                <div
                  className="execution-timeline__progress-bar"
                  style={{ width: `${event.metadata.progress * 100}%` }}
                  role="progressbar"
                  aria-valuenow={Math.round(event.metadata.progress * 100)}
                  aria-valuemin={0}
                  aria-valuemax={100}
                />
              </div>
            )}
          </div>
        </article>
      ))}
    </div>
  );
};

const SkeletonTimeline: React.FC = () => (
  <div className="skeleton-timeline" aria-busy="true" aria-label="Loading timeline">
    {Array.from({ length: 3 }).map((_, i) => (
      <div key={i} className="skeleton-timeline__item">
        <Skeleton width="12px" height="12px" borderRadius="50%" />
        <div className="skeleton-timeline__content">
          <Skeleton width="40%" height="0.875rem" />
          <Skeleton width="80%" height="0.75rem" />
        </div>
      </div>
    ))}
  </div>
);