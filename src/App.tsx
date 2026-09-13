import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Route, Routes, Navigate } from "react-router-dom";
import axios from "axios";
import "./App.css";
import ErrorBoundary from "./components/ErrorBoundary";
import ProjectList from "./pages/ProjectList";
import ProjectDetail from "./pages/ProjectDetail";
import TaskList from "./pages/TaskList";
import TaskDetail from "./pages/TaskDetail";
import Dashboard from "./pages/Dashboard";
import Activity from "./pages/Activity";
import WorkersPage from "./pages/WorkersPage";
import WorkerDetail from "./pages/WorkerDetail";
import Navigation from "./components/Navigation";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Settings from "./pages/Settings";
import AgentsPage from "./pages/AgentsPage";
import Welcome from "./pages/Welcome";
import { LanguageProvider } from "./context/LanguageContext";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

/** Simple authentication check wrapper without provider gate (e.g. for /welcome onboarding) */
function RequireAuth({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        setIsAuthenticated(false);
        setLoading(false);
        return;
      }
      try {
        const res = await axios.get(`${API_BASE}/auth/me`, {
          timeout: 5000,
          headers: { Authorization: `Bearer ${token}` },
          withCredentials: true,
        });
        const hasUser = !!(res.data && (res.data.user || res.data.id || res.data.email));
        setIsAuthenticated(hasUser);
        if (hasUser) {
          const userEmail = res.data?.email || res.data?.user?.email;
          if (userEmail) {
            localStorage.setItem("user_email", userEmail);
          }
        } else {
          localStorage.removeItem("token");
          localStorage.removeItem("user_email");
        }
      } catch {
        localStorage.removeItem("token");
        localStorage.removeItem("user_email");
        setIsAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };
    checkAuth();
  }, []);

  if (loading) {
    return <div className="loading-spinner" role="status">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

/** Full route protection: ensures user is authenticated AND has configured an AI provider */
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [hasProvider, setHasProvider] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        setIsAuthenticated(false);
        setLoading(false);
        return;
      }
      try {
        const res = await axios.get(`${API_BASE}/auth/me`, {
          timeout: 5000,
          headers: { Authorization: `Bearer ${token}` },
          withCredentials: true,
        });
        const userData = res.data?.user || res.data;
        const hasUser = !!(res.data && (res.data.user || res.data.id || res.data.email));
        setIsAuthenticated(hasUser);
        if (hasUser) {
          const userEmail = userData?.email;
          if (userEmail) {
            localStorage.setItem("user_email", userEmail);
          }
          // Check if AI provider has been configured
          setHasProvider(userData?.has_configured_provider ?? false);
        } else {
          localStorage.removeItem("token");
          localStorage.removeItem("user_email");
        }
      } catch {
        localStorage.removeItem("token");
        localStorage.removeItem("user_email");
        setIsAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };
    checkAuth();
  }, []);

  if (loading) {
    return <div className="loading-spinner" role="status">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Intercept users who have not yet configured an AI provider
  if (hasProvider === false) {
    return <Navigate to="/welcome" replace />;
  }

  return <>{children}</>;
}

function App() {
  // Check backend availability on app load
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const res = await axios.get(`${API_BASE}/`, { timeout: 5000 });
        console.log("Backend health check:", res.data.status);
      } catch (err: any) {
        console.warn("Backend unreachable:", err?.message);
      }
    };
    checkBackend();
  }, []);

  return (
    <LanguageProvider>
      <Router>
        <div className="app">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route
              path="/welcome"
              element={
                <RequireAuth>
                  <Welcome />
                </RequireAuth>
              }
            />
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <Navigation />
                  <main className="app__main">
                    <ErrorBoundary>
                      <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/activity" element={<Activity />} />
                        <Route path="/settings" element={<Settings />} />
                        <Route path="/agents" element={<AgentsPage />} />
                        <Route path="/workers" element={<WorkersPage />} />
                        <Route path="/workers/:id" element={<WorkerDetail />} />
                        <Route path="/projects" element={<ProjectList />} />
                        <Route path="/projects/:projectId" element={<ProjectDetail />} />
                        <Route path="/tasks/:projectId" element={<TaskList />} />
                        <Route path="/projects/:projectId/tasks/:taskId" element={<TaskDetail />} />
                      </Routes>
                    </ErrorBoundary>
                  </main>
                </ProtectedRoute>
              }
            />
          </Routes>
        </div>
      </Router>
    </LanguageProvider>
  );
}

export default App;