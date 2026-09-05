import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Project } from "../types";
import { projectApi } from "../services/api";
import { TaskList } from "../components/TaskList";
import { TaskDetail } from "../components/TaskDetail";
import Loading from "../components/Loading";
import "./ProjectWorkspace.css";

const ProjectWorkspace: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"list" | "detail">("list");

  const fetchProject = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await projectApi.getById(projectId);
      setProject(data);
    } catch (err: any) {
      setError(err.detail || "Failed to load project");
      if (err.detail?.includes("not found")) {
        navigate("/projects");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (projectId) {
      fetchProject();
      setViewMode("list");
      setActiveTaskId(null);
    }
  }, [projectId]);

  const handleTaskSelect = (taskId: string) => {
    setActiveTaskId(taskId);
    setViewMode("detail");
  };

  const handleBackToList = () => {
    setViewMode("list");
    setActiveTaskId(null);
  };

  const handleTaskUpdate = (taskId: string, updates: Partial<any>) => {
    // In a real implementation, this would call the update API
    // For now, we'll optimistically update the local state
    setTasks((prev) => prev.map((t) => (t.id === taskId ? { ...t, ...updates } : t)));
  };

  if (loading && !project) {
    return <Loading message="Loading project workspace..." />;
  }

  if (error && !project) {
    return (
      <div className="project-workspace">
        <div className="alert alert-error" role="alert">
          <span>{error}</span>
          <button className="btn btn-outline btn-sm" onClick={() => navigate("/projects")}>
            Back to Projects
          </button>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="project-workspace">
        <div className="alert alert-error" role="alert">
          Project not found.
        </div>
      </div>
    );
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="project-workspace">
      <header className="project-workspace__header">
        <button className="btn btn-outline btn-sm" onClick={() => navigate("/projects")}>
          ← Back to Projects
        </button>
        <div className="project-workspace__title-section">
          <h1 className="project-workspace__title">{project.name}</h1>
          <p className="project-workspace__meta">
            <span>ID: {project.id.slice(0, 8)}...</span>
            <span>•</span>
            <span>Created {formatDate(project.created_at)}</span>
            <span>•</span>
            <span>Updated {formatDate(project.updated_at)}</span>
          </p>
        </div>
      </header>

      {viewMode === "list" ? (
        <TaskList
          projectId={projectId}
          onTaskSelect={handleTaskSelect}
        />
      ) : (
        <TaskDetail
          taskId={activeTaskId}
          projectId={projectId}
          onBack={handleBackToList}
          onTaskUpdate={handleTaskUpdate}
        />
      )}
    </div>
  );
};

export default ProjectWorkspace;