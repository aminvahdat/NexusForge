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
import { LanguageProvider } from "./context/LanguageContext";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      // Fast path: token present in localStorage (set by Login/Register)
      if (localStorage.getItem("token")) {
        try {
          const res = await axios.get(`${API_BASE}/auth/me`, { timeout: 5000, withCredentials: true });
          setIsAuthenticated(!!res.data.user);
        } catch {
          setIsAuthenticated(true); // token exists; let backend verify on real requests
        } finally {
          setLoading(false);
        }
        return;
      }
      try {
        const res = await axios.get(`${API_BASE}/auth/me`, { timeout: 5000, withCredentials: true });
        setIsAuthenticated(!!res.data.user);
      } catch (err) {
        setIsAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };
    checkAuth();
  }, [API_BASE]);

  if (loading) {
    return <div className="loading-spinner" role="status">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function App() {
  // Check backend availability on app load
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const res = await axios.get(`${API_BASE}/`, { timeout: 5000 });
        console.log("Backend health check:", res.data.status);
      } catch (err) {
        console.warn("Backend unreachable:", err.message);
      }
    };
    checkBackend();
  }, [API_BASE]);

  return (
    <LanguageProvider>
      <Router>
        <div className="app">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
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