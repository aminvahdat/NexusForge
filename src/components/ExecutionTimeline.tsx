import React, { useRef, useEffect } from "react";
import { ExecutionEvent } from "../types";
import { Skeleton } from "./Skeleton";
import "./ExecutionTimeline.css";

/* ExecutionTimeline — Phase 5.5 Enhanced Real-Time Timeline
   - Chronological events with readable timestamps
   - Event category styling with clear visual hierarchy
   - Accessibility: semantic HTML, aria-labels, keyboard navigation
   - Reduced motion: no animations when prefers-reduced-motion is set
   - Only animate new events, not the entire timeline
   - Performance: virtualization-ready for large event lists
   - Event deduplication using stable event IDs
*/

interface ExecutionTimelineProps {
  events: ExecutionEvent[];
  isLoading?: boolean;
  maxEvents?: number;  // Performance limit for event list
  showWorker?: boolean;
  showExecution?: boolean;
  className?: string;
  onEventClick?: (event: ExecutionEvent) => void;
}

/* Event category classification for styling */
type EventCategory = "execution" | "worker" | "progress" | "error" | "system";

function classifyEvent(eventType: string): EventCategory {
  const type = eventType.toLowerCase();
  if (type.includes("execution")) return "execution";
  if (type.includes("worker")) return "worker";
  if (type.includes("progress")) return "progress";
  if (type.includes("error") || type.includes("fail")) return "error";
  return "system";
}

/* Icon mapping for event types (accessible, no emoji in aria) */
const eventIcons: Record<string, string> = {
  "execution_created": "▶",
  "execution_queued": "⏳",
  "worker_assigned": "👤",
  "execution_started": "▶",
  "progress_update": "📊",
  "execution_completed": "✅",
  "execution_failed": "❌",
  "execution_cancelled": "🛑",
  "worker_heartbeat": "💓",
};

function getEventIcon(eventType: string): string {
  return eventIcons[eventType] || "•";
}

/* Format timestamp to readable time */
function formatTime(timestamp: string | Date): string {
  const date = typeof timestamp === "string" ? new Date(timestamp) : timestamp;
  return date.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

/* Format relative time */
function formatRelativeTime(timestamp: string | Date): string {
  const date = typeof timestamp === "string" ? new Date(timestamp) : timestamp;
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  
  if (diffSec < 60) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHour < 24) return `${diffHour}h ago`;
  return date.toLocaleDateString();
}

/* Check for reduced motion preference */
function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = React.useState(false);
  
  React.useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    
    const listener = (e: MediaQueryListEvent) => setReduced(e.matches);
    mq.addEventListener("change", listener);
    return () => mq.removeEventListener("change", listener);
  }, []);
  
  return reduced;
}

/* Event item component with animation for new events */
const TimelineEvent: React.FC<{
  event: ExecutionEvent;
  showWorker?: boolean;
  showExecution?: boolean;
  isNew?: boolean;
  reducedMotion: boolean;
  onClick?: (e: ExecutionEvent) => void;
}> = ({ event, showWorker, showExecution, isNew, reducedMotion, onClick }) => {
  const eventRef = useRef<HTMLDivElement>(null);
  const category = classifyEvent(event.event_type);
  
  /* Auto-scroll for new events (only if user hasn't scrolled) */
  useEffect(() => {
    if (isNew && eventRef.current && !reducedMotion) {
      const el = eventRef.current;
      const container = el.closest(".execution-timeline");
      if (container) {
        const isAtBottom = 
          container.scrollHeight - container.scrollTop <= container.clientHeight + 100;
        if (isAtBottom) {
          el.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
      }
    }
  }, [isNew, reducedMotion]);
  
  const categoryClass = `timeline-event--${category}`;
  const newClass = isNew && !reducedMotion ? "timeline-event--new" : "";
  const animationClass = isNew && !reducedMotion ? "timeline-event-animate-in" : "";
  
  return (
    <div
      ref={eventRef}
      className={`timeline-event ${categoryClass} ${newClass} ${animationClass}`}
      role="listitem"
      aria-label={`${event.event_type}: ${event.message || ""}`}
      onClick={() => onClick?.(event)}
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick?.(event);
        }
      }}
    >
      {/* Timeline connector */}
      <div className="timeline-event__connector" aria-hidden="true">
        <div className={`timeline-event__dot timeline-event__dot--${category}`} />
      </div>
      
      {/* Event content */}
      <div className="timeline-event__content">
        <div className="timeline-event__header">
          {/* Icon */}
          <span className="timeline-event__icon" aria-hidden="true">
            {getEventIcon(event.event_type)}
          </span>
          
          {/* Event type label */}
          <span className="timeline-event__type" aria-hidden="true">
            {event.event_type.replace(/_/g, " ")}
          </span>
          
          {/* Time */}
          <time
            className="timeline-event__time"
            dateTime={String(event.timestamp)}
            title={formatTime(event.timestamp)}
          >
            {formatRelativeTime(event.timestamp)}
          </time>
        </div>
        
        {/* Event message */}
        {event.message && (
          <p className="timeline-event__message">
            {event.message}
          </p>
        )}
        
        {/* Event metadata */}
        <div className="timeline-event__meta">
          {/* Worker info */}
          {showWorker && event.worker_id && (
            <span className="timeline-event__worker" aria-label={`Worker: ${event.worker_id}`}>
              👤 {event.worker_id.slice(0, 8)}...
            </span>
          )}
          
          {/* Execution info */}
          {showExecution && event.execution_id && (
            <span className="timeline-event__execution" aria-label={`Execution: ${event.execution_id}`}>
              ⚡ {event.execution_id.slice(0, 8)}...
            </span>
          )}
          
          {/* Event ID */}
          {event.id && (
            <span className="timeline-event__id" aria-hidden="true">
              #{event.id.slice(0, 8)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

/* Skeleton loading state */
const TimelineSkeleton: React.FC<{ count?: number }> = ({ count = 5 }) => (
  <div className="execution-timeline__skeleton" role="status" aria-label="Loading timeline">
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="timeline-skeleton-item">
        <div className="timeline-skeleton-item__connector">
          <Skeleton width="12px" height="12px" borderRadius="50%" />
        </div>
        <div className="timeline-skeleton-item__content">
          <Skeleton width="120px" height="14px" />
          <Skeleton width="200px" height="12px" />
        </div>
      </div>
    ))}
  </div>
);

/* Empty state */
const TimelineEmpty: React.FC = () => (
  <div className="execution-timeline__empty" role="status">
    <div className="execution-timeline__empty-icon" aria-hidden="true">📋</div>
    <p className="execution-timeline__empty-title">No events yet</p>
    <p className="execution-timeline__empty-description">
      Execution events will appear here in real-time as your tasks run.
    </p>
  </div>
);

/* Main ExecutionTimeline component */
export const ExecutionTimeline: React.FC<ExecutionTimelineProps> = ({
  events,
  isLoading = false,
  maxEvents = 100,  // Performance limit
  showWorker = true,
  showExecution = true,
  className = "",
  onEventClick,
}) => {
  const reducedMotion = usePrefersReducedMotion();
  const listRef = useRef<HTMLDivElement>(null);
  const seenEventIds = useRef<Set<string>>(new Set());
  const [newEventIds, setNewEventIds] = React.useState<Set<string>>(new Set());
  
  /* Deduplicate events by ID */
  const deduplicatedEvents = React.useMemo(() => {
    const deduped: ExecutionEvent[] = [];
    for (const event of events) {
      const eventId = event.id || `${event.event_type}-${event.timestamp}`;
      if (!seenEventIds.current.has(eventId)) {
        seenEventIds.current.add(eventId);
        deduped.push(event);
      }
    }
    return deduped;
  }, [events]);
  
  /* Limit events for performance */
  const displayEvents = React.useMemo(() => {
    const limited = deduplicatedEvents.slice(-maxEvents);
    return limited;
  }, [deduplicatedEvents, maxEvents]);
  
  /* Track new events */
  React.useEffect(() => {
    const latestIds = new Set(displayEvents.map((e) => e.id || `${e.event_type}-${e.timestamp}`));
    const newIds = new Set<string>();
    
    latestIds.forEach((id) => {
      if (!seenEventIds.current.has(id)) {
        newIds.add(id);
        seenEventIds.current.add(id);
      }
    });
    
    if (newIds.size > 0) {
      setNewEventIds((prev) => new Set([...prev, ...newIds]));
      
      /* Clear "new" status after animation completes */
      const timer = setTimeout(() => {
        setNewEventIds((prev) => {
          const updated = new Set(prev);
          newIds.forEach((id) => updated.delete(id));
          return updated;
        });
      }, 1000);
      
      return () => clearTimeout(timer);
    }
  }, [displayEvents]);
  
  /* Keyboard navigation */
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      const items = listRef.current?.querySelectorAll("[role=listitem]");
      if (!items || items.length === 0) return;
      
      const currentIndex = Array.from(items).findIndex(
        (item) => item === document.activeElement
      );
      
      let nextIndex: number;
      if (e.key === "ArrowDown") {
        nextIndex = Math.min(currentIndex + 1, items.length - 1);
      } else {
        nextIndex = Math.max(currentIndex - 1, 0);
      }
      
      (items[nextIndex] as HTMLElement).focus();
    }
  };
  
  return (
    <div
      className={`execution-timeline ${className}`}
      role="list"
      aria-label="Execution timeline"
      aria-busy={isLoading}
      ref={listRef}
      onKeyDown={handleKeyDown}
    >
      {/* Timeline header */}
      <div className="execution-timeline__header">
        <h3 className="execution-timeline__title">Activity Timeline</h3>
        <span className="execution-timeline__count" aria-label={`${displayEvents.length} events`}>
          {displayEvents.length} event{displayEvents.length !== 1 ? "s" : ""}
        </span>
      </div>
      
      {/* Timeline content */}
      <div className="execution-timeline__events">
        {isLoading ? (
          <TimelineSkeleton count={5} />
        ) : displayEvents.length === 0 ? (
          <TimelineEmpty />
        ) : (
          displayEvents.map((event) => (
            <TimelineEvent
              key={event.id || `${event.event_type}-${event.timestamp}`}
              event={event}
              showWorker={showWorker}
              showExecution={showExecution}
              isNew={newEventIds.has(event.id || `${event.event_type}-${event.timestamp}`)}
              reducedMotion={reducedMotion}
              onClick={onEventClick}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default ExecutionTimeline;