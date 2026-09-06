import React from "react";
import { Link } from "react-router-dom";

/* Empty state component for when no executions exist */
interface EmptyStateProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  action?: {
    label: string;
    to: string;
  };
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon,
  action,
}) => (
  <div className="empty-state" role="status">
    {icon && <div className="empty-state__icon" aria-hidden="true">{icon}</div>}
    <h3 className="empty-state__title">{title}</h3>
    <p className="empty-state__description">{description}</p>
    {action && (
      <Link to={action.to} className="btn btn-primary btn-sm">
        {action.label}
      </Link>
    )}
  </div>
);
