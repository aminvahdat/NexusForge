import React, { Component, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  error?: Error | null;
  errorInfo?: React.ErrorInfo | null;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.warn("UI Error caught:", error, info);
    this.setState({ errorInfo: info });
  }

  render() {
    if (this.state.hasError) {
      const e = this.state.error;
      const info = this.state.errorInfo;
      return (
        <div style={{ padding: 24, color: '#f87171', background: '#0f172a', fontFamily: 'monospace' }}>
          <h2>Component Render Crash</h2>
          <p><strong>Message:</strong> {e?.name}: {e?.message}</p>
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: '12px' }}>{e?.stack}</pre>
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: '12px', color: '#94a3b8' }}>{info?.componentStack}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
