import React from "react";
import "./Skeleton.css";

interface SkeletonProps {
  width?: string;
  height?: string;
  borderRadius?: string;
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = "100%",
  height = "1rem",
  borderRadius = "6px",
  className = "",
}) => (
  <div
    className={`skeleton ${className}`}
    style={{ width, height, borderRadius }}
    aria-hidden="true"
  />
);

export const SkeletonCard: React.FC = () => (
  <div className="skeleton-card">
    <Skeleton width="40%" height="1.5rem" />
    <Skeleton width="100%" height="1rem" />
    <Skeleton width="80%" height="1rem" />
    <div className="skeleton-card__footer">
      <Skeleton width="30%" height="0.875rem" />
      <Skeleton width="20%" height="0.875rem" />
    </div>
  </div>
);

export const SkeletonTimeline: React.FC<{ count?: number }> = ({ count = 4 }) => (
  <div className="skeleton-timeline">
    {Array.from({ length: count }).map((_, i) => (
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