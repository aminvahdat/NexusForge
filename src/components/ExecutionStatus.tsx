import React, { useState, useEffect } from "react";
import { ExecutionStatus, WorkerStatus } from "../types";
import { Skeleton } from "./Skeleton";

interface ExecutionStatusProps {
  status: string;
  error?: string;
  onRefresh?: () => void;
  isLive?: boolean;
  connected?: boolean;
}

export const ExecutionStatus: React.FC<ExecutionStatusProps> = ({
  status,
  error,
  onRefresh,
  isLive = false,
  connected = true,
}) => {
  const [isPulsing, setIsPulsing] = useState(false);

  // Trigger pulse animation on status change
  useEffect(() => {
    if (isLive) {
      setIsPulsing(true);
      const timer = setTimeout(() => setIsPulsing(false), 1000);
      return () => clearTimeout(timer);
    }
  }, [status, isLive]);

  const statusMap: Record<string, string> = {
    queued: "Queued",
    pending: "Pending",
    assigned: "Assigned",
    running: "Running",
    working: "Working",
    blocked: "Blocked",
    reviewing: "Reviewing",
    completed: "Completed",
    failed: "Failed",
    cancelled: "Cancelled",
  };

  const statusLabel = statusMap[status] || status;
  const statusColors: Record<string, string> = {
    completed: "#10b981",
    failed: "#ef4444",
    cancelled: "#6b7280",
    running: "#f59e0b",
    queued: "#3b82f6",
    blocked: "#8b5cf6",
    default: "#6b7280",
  };

  const color = statusColors[status] || statusColors.default;
  const isRunning = status === "running" || status === "working";

  return (
    <div
      className={`execution-status ${isPulsing ? "execution-status--live" : ""}`}
      aria-live="polite"
    >
      <span className="execution-status__label">Status:</span>
      <span
        className="execution-status__badge"
        style={{ color, backgroundColor: `${color}15` }}
      >
        {isRunning && (
          <span
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              backgroundColor: color,
              animation: "live-pulse 2s ease-in-out infinite",
            }}
            aria-hidden="true"
          />
        )}
        {statusLabel}
      </span>
      {error && (
        <span className="execution-status__error">{error}</span>
      )}
      {onRefresh && (
        <button
          className="execution-status__refresh"
          onClick={onRefresh}
          title="Refresh status"
          aria-label="Refresh execution status"
        >
          ↻
        </button>
      )}
      <span
        className={`connection-indicator ${
          connected ? "connection-indicator--connected" : "connection-indicator--disconnected"
        }`}
        aria-label={connected ? "WebSocket connected" : "WebSocket disconnected"}
      >
        <span
          style={{
            width: "8px",
            height: "8px",
            borderRadius: "50%",
            backgroundColor: connected ? "#10b981" : "#ef4444",
          }}
          aria-hidden="true"
        />
        {connected ? "Live" : "Reconnecting"}
      </span>
    </div>
  );
};

export const ExecutionStatusSkeleton: React.FC = () => (
  <div className="execution-status">
    <Skeleton width="60px" height="1rem" />
    <Skeleton width="80px" height="1.5rem" borderRadius="9999px" />
    <Skeleton width="50px" height="0.875rem" />
  </div>
);