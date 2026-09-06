import React, { useState, useEffect, useRef } from "react";
import "./Toast.css";

/* Toast / Notification System — Phase 5.5
   Lightweight, reusable notification mechanism with:
   - Multiple severity levels (success, error, warning, info)
   - Auto-dismiss after configurable timeout
   - Click-to-dismiss
   - Accessible: aria-live, keyboard navigation
   - Prevent duplicate notifications for same event
   - Ordered queue for multiple notifications
   - Only meaningful events, not spam
*/

interface ToastProps {
  id: string;
  title: string;
  description?: string;
  severity?: "success" | "error" | "warning" | "info";
  action?: {
    label: string;
    onClick: () => void;
  };
  timeout?: number;
  closeable?: boolean;
}

interface ToastState {
  id: string;
  title: string;
  description?: string;
  severity: "success" | "error" | "warning" | "info";
  action?: { label: string; onClick: () => void };
  timeout?: number;
  closeable?: boolean;
  elapsed: number;
}

/* Toast queue — notifications are queued and displayed one at a time */
const toastQueue: ToastState[] = [];
let nextId = 1;

/* Generate unique toast ID */
function useToastId(): string {
  const id = `toast-${nextId++}`;
  return id;
}

/* Show a toast notification */
function useShowToast(): (params: Omit<ToastProps, "id">) => string {
  const [toasts, setToasts] = useState<ToastState[]>([]);

  const showToast = (params: Omit<ToastProps, "id">) => {
    const id = useToastId();
    const now = Date.now();
    const toast: ToastState = {
      id,
      title: params.title,
      description: params.description,
      severity: params.severity ?? "info",
      action: params.action,
      timeout: params.timeout,
      closeable: params.closeable ?? true,
      elapsed: 0,
    };

    setToasts((prev) => {
      /* Prevent duplicate notifications */
      if (prev.some((t) => t.title === params.title && t.severity === params.severity)) {
        return prev;
      }

      const newQueue = [toast, ...prev].slice(0, 3); // Max 3 concurrent
      setToasts(newQueue);

      /* Auto-dismiss */
      if (toast.timeout && toast.timeout > 0) {
        const timer = setTimeout(() => {
          setToasts((prev) => prev.filter((t) => t.id !== id));
        }, toast.timeout);
      }

      return newQueue;
    });
  };

  /* Auto-cleanup finished toasts */
  useEffect(() => {
    const activeToasts = toasts.filter((t) => {
      if (!t.timeout) return true;
      /* Already dismissed via timeout */
      return t.elapsed < (t.timeout || 10000);
    });

    /* Optional: visual progress tracking */
    const interval = setInterval(() => {
      setToasts((prev) =>
        prev.map((t) => ({
          ...t,
          elapsed: t.elapsed + 100,
        }))
      );
    }, 100);

    return () => {
      clearInterval(interval);
    };
  }, [toasts]);

  return { showToast, toasts };
}

/* Toast component */
const Toast: React.FC<ToastProps> = ({ id, title, description, severity = "info", action, timeout = 5000, closeable = true }) => {
  const [show, setShow] = useState(true);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!show) return;
    if (timeout && timeout > 0) {
      const timer = setTimeout(() => setShow(false), timeout);
      return () => clearTimeout(timer);
    }
  }, [show, timeout]);

  /* Keyboard handler */
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      setShow(false);
    }
    if (e.key === "Enter" && action && show) {
      e.preventDefault();
      action?.onClick();
    }
  };

  return (
    <div
      className={`toast toast--${severity} ${show ? "toast--visible" : "toast--hidden"}`}
      role="alert"
      aria-live="polite"
      aria-atomic="true"
      aria-label={title}
      onClick={() => setShow(false)}
      onKeyDown={handleKeyDown}
    >
      <div className="toast__content">
        <div className={`toast__icon toast__icon--${severity}`} aria-hidden="true" />
        <div className="toast__details">
          <p className="toast__title">{title}</p>
          {description && <p className="toast__description">{description}</p>}
        </div>
      </div>
      <button
        className="toast__close"
        onClick={(e) => { e.stopPropagation(); setShow(false); }}
        aria-label="Close toast"
        title="Close"
        role="button"
      >
        ×
      </button>
    </div>
  );
};

/* ToastProvider — provides showToast hook */
export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const { showToast, toasts } = useShowToast();

  return (
    <div className="toast-container">
      {toasts.map((toast) => (
        <Toast key={toast.id} {...toast} />
      ))}
      {children}
    </div>
  );
};

/* Hook to use toast notifications */
export const useToast = () => {
  return useShowToast();
};

export default Toast;