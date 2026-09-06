import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import axios from "axios";
import "./App.css";

import ProjectList from "./pages/ProjectList";
import ProjectDetail from "./pages/ProjectDetail";
import TaskList from "./pages/TaskList";
import TaskDetail from "./pages/TaskDetail";
import Dashboard from "./pages/Dashboard";
import Activity from "./pages/Activity";
import WorkersPage from "./pages/WorkersPage";
import WorkerDetail from "./pages/WorkerDetail";
import Navigation from "./components/Navigation";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

function App() {
  const navigate = useNavigate();
  const location = useLocation();

  // Check backend availability on app load
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const res = await axios.get(`${API_BASE}/api/health`, { timeout: 5000 });
        console.log("Backend health check:", res.data.status);
      } catch (err) {
        console.warn("Backend unreachable:", err.message);
      }
    };
    checkBackend();
  }, [API_BASE]);

  // Check auth token - this is a placeholder for Phase 3 auth integration
  const [authToken, setAuthToken] = useState<string | null>(null);

  return (
    <Router>
      <div className="app">
        <Navigation />
        
        <main className="app__main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/activity" element={<Activity />} />
            <Route path="/workers" element={<WorkersPage />} />
            <Route path="/workers/:id" element={<WorkerDetail />} />
            <Route path="/projects" element={<ProjectList />} />
            <Route path="/projects/:projectId" element={<ProjectDetail />} />
            <Route path="/tasks/:projectId" element={<TaskList />} />
            <Route path="/projects/:projectId/tasks/:taskId" element={<TaskDetail />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;