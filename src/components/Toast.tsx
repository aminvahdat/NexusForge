import React from "react";

interface ToastProps {
  message: string;
  type?: "success" | "error" | "info";
  title?: string;
  onClose?: () => void;
}

export const Toast: React.FC<ToastProps> = ({
  message,
  type = "info",
  title,
  onClose,
}) => {
  const iconMap = {
    success: "✓",
    error: "✗",
    info: "ℹ",
  };

  return (
    <div className={`toast toast--${type}`} role="alert">
      <span className="toast__icon" aria-hidden="true">{iconMap[type]}</span>
      <div className="toast__content">
        {title && <h4 className="toast__title">{title}</h4>}
        <p className="toast__message">{message}</p>
      </div>
      {onClose && (
        <button className="toast__close" onClick={onClose} aria-label="Close notification">
          ×
        </button>
      )}
    </div>
  );
};

export const ToastContainer: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  return <div className="toast-container" aria-live="polite">{children}</div>;
};
