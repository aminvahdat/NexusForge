import React from "react";
import { Task, TaskCreate, TaskStatus, AgentRole, Priority } from "../types";

interface TaskListProps {
  projectId?: string;
  tasks: Task[];
  onTaskSelect?: (task: Task) => void;
  onStatusChange?: (taskId: string, newStatus: string) => void;
}

const statusColors: Record<string, string> = {
  queued: "status-queued",
  planning: "status-planning",
  blocked: "status-blocked",
  ready: "status-ready",
  running: "status-running",
  waiting: "status-waiting",
  reviewing: "status-reviewing",
  needs_revision: "status-needs-revision",
  completed: "status-completed",
  failed: "status-failed",
  cancelled: "status-cancelled",
};

const priorityIcons: Record<string, string> = {
  low: "●",
  medium: "◐",
  high: "▲",
  critical: "■",
};

const formatDate = (dateString: string | null) => {
  if (!dateString) return "-";
  return new Date(dateString).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const getRoleLabel = (role: string) => {
  return role.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
};

export const TaskList: React.FC<TaskListProps> = ({
  projectId,
  tasks,
  onTaskSelect,
  onStatusChange,
}: TaskListProps) => {
  const renderTaskCard = (task: Task) => {
    const isSelectable = !!onTaskSelect;
    const Card = isSelectable ? "article" : "div";
    const cardProps = isSelectable
      ? {
          onClick: () => onTaskSelect?.(task),
          role: "button",
          tabIndex: 0,
          onKeyDown: (e: React.KeyboardEvent) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              onTaskSelect?.(task);
            }
          },
        }
      : {};

    const canTransition =
      !["completed", "failed", "cancelled"].includes(task.status);

    return (
      <Card
        key={task.id}
        className="task-card"
        {...cardProps}
      >
        <div className="task-card__main">
          <header className="task-card__header">
            <h4 className="task-card__title">{task.title}</h4>
            <span className={`priority-badge priority-badge--${task.priority}`}>
              {priorityIcons[task.priority] || "●"} {task.priority}
            </span>
          </header>
          <div className="task-card__meta">
            <span className={`status-badge ${statusColors[task.status] || "status-queued"}`}>
              {task.status.replace(/_/g, " ")}
            </span>
            <span className="role-badge">{getRoleLabel(task.role)}</span>
          </div>
          {task.description && (
            <p className="task-card__description">
              {task.description.length > 200
                ? `${task.description.substring(0, 200)}...`
                : task.description}
            </p>
          )}
          {task.acceptance_criteria && task.acceptance_criteria.length > 0 && (
            <ul className="task-card__criteria">
              {task.acceptance_criteria.slice(0, 3).map((criterion, index) => (
                <li key={index} className="task-card__criterion">
                  <span>✓</span> {criterion}
                </li>
              ))}
              {task.acceptance_criteria.length > 3 && (
                <li className="task-card__more">
                  +{task.acceptance_criteria.length - 3} more
                </li>
              )}
            </ul>
          )}
        </div>

        {canTransition && onStatusChange && (
          <div className="task-card__actions">
            <select
              className="input input--small"
              value={task.status}
              onChange={(e) => onStatusChange(task.id, e.target.value)}
              aria-label={`Change status for ${task.title}`}
              onClick={(e) => e.stopPropagation()}
            >
              <option value="queued">Queued</option>
              <option value="planning">Planning</option>
              <option value="ready">Ready</option>
              <option value="running">Running</option>
              <option value="waiting">Waiting</option>
              <option value="reviewing">Reviewing</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        )}

        <footer className="task-card__footer">
          <time className="task-card__time" dateTime={task.created_at}>
            {formatDate(task.created_at)}
          </time>
          {task.retry_count > 0 && (
            <span className="task-card__retries" title="Retry count">
              ↻ {task.retry_count}/{task.max_retries}
            </span>
          )}
          {task.due_date && (
            <time className="task-card__due" dateTime={task.due_date} title="Due date">
              Due {formatDate(task.due_date)}
            </time>
          )}
        </footer>
      </Card>
    );
  };

  if (!tasks || tasks.length === 0) {
    return (
      <div className="empty-state">
        <svg
          className="empty-state__icon"
          width="48"
          height="48"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
        >
          <line x1="12" y1="20" x2="12" y2="4"></line>
          <polyline points="6 10 12 16 18 10"></polyline>
        </svg>
        <h3 className="empty-state__title">No Tasks Yet</h3>
        <p className="empty-state__description">
          Create your first task to start building with this project.
        </p>
      </div>
    );
  }

  return (
    <div className="task-list">
      {tasks.map(renderTaskCard)}
    </div>
  );
};

export default TaskList;