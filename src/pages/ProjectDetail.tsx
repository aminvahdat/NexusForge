import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Project, Task, TaskCreate, TaskStatus, AgentRole, Priority } from "../types";
import { projectApi, taskApi } from "../services/api";
import Loading from "../components/Loading";
import ProjectTaskForm from "../components/ProjectTaskForm";
import TaskList from "../components/TaskList";


const ProjectDetail: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [taskFormData, setTaskFormData] = useState<TaskCreate>({
    project_id: projectId,
    title: "",
    description: "",
    role: AgentRole.PROJECT_PLANNER,
    required_skills: [],
    dependencies: [],
    input_artifacts: [],
    output_artifacts: [],
    acceptance_criteria: [],
    priority: Priority.MEDIUM,
    status: TaskStatus.QUEUED,
    retry_count: 0,
    max_retries: 3,
    due_date: null,
  });

  const fetchProject = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await projectApi.getById(projectId);
      setProject(data);
    } catch (err: any) {
      setError(err.detail || "Failed to load project");
      // Handle not found
      if (err.detail?.includes("not found")) {
        navigate("/projects");
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchTasks = async () => {
    try {
      const data = await taskApi.getAllByProject(projectId);
      setTasks(data);
    } catch (err: any) {
      setError(err.detail || "Failed to load tasks");
    }
  };

  const handleTaskCreate = async (taskData: TaskCreate) => {
    try {
      const newTask = await taskApi.create(projectId, taskData);
      setTasks((prev) => [...prev, newTask]);
      setShowTaskModal(false);
      // Reset form
      setTaskFormData({
        project_id: projectId,
        title: "",
        description: "",
        role: AgentRole.PROJECT_PLANNER,
        required_skills: [],
        dependencies: [],
        input_artifacts: [],
        output_artifacts: [],
        acceptance_criteria: [],
        priority: Priority.MEDIUM,
        status: TaskStatus.QUEUED,
        retry_count: 0,
        max_retries: 3,
        due_date: null,
      });
    } catch (err: any) {
      setError(err.detail || "Failed to create task");
    }
  };

  const handleTaskUpdate = (taskId: string, updates: Partial<Task>) => {
    // In a real implementation, this would call the update API
    // For now, we'll optimistically update the local state
    setTasks((prev) =>
      prev.map((task) => (task.id === taskId ? { ...task, ...updates } : task))
    );
  };

  useEffect(() => {
    if (projectId) {
      fetchProject();
      fetchTasks();
    }
  }, [projectId]);

  if (loading && !project) {
    return <Loading message="Loading project..." />;
  }

  if (error && !project) {
    return (
      <div className="project-detail">
        <div className="alert alert-error" role="alert">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
          <span>{error}</span>
          <button
            className="btn btn-outline"
            onClick={() => {
              setError(null);
              navigate("/projects");
            }}
          >
            Back to Projects
          </button>
        </div>
      </div>
    );
  }

  if (!project) {
    return <div className="project-detail">Loading...</div>;
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case "queued":
        return "bg-slate-100 text-slate-700 border-slate-300";
      case "planning":
        return "bg-blue-100 text-blue-700 border-blue-300";
      case "blocked":
        return "bg-red-100 text-red-700 border-red-300";
      case "ready":
        return "bg-yellow-100 text-yellow-700 border-yellow-300";
      case "running":
        return "bg-indigo-100 text-indigo-700 border-indigo-300";
      case "waiting":
        return "bg-purple-100 text-purple-700 border-purple-300";
      case "reviewing":
        return "bg-teal-100 text-teal-700 border-teal-300";
      case "needs_revision":
        return "bg-orange-100 text-orange-700 border-orange-300";
      case "completed":
        return "bg-green-100 text-green-700 border-green-300";
      case "failed":
        return "bg-red-100 text-red-700 border-red-300";
      case "cancelled":
        return "bg-gray-100 text-gray-700 border-gray-300";
      default:
        return "bg-gray-100 text-gray-700 border-gray-300";
    }
  };

  return (
    <div className="project-detail">
      <header className="project-detail__header">
        <div className="project-detail__header-left">
          <button
            className="btn btn-outline"
            onClick={() => navigate("/projects")}
            aria-label="Back to projects"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="5" y1="12" x2="19" y2="12"></line>
              <polyline points="12 5 5 12 12 19"></polyline>
            </svg>
          </button>
          <h1 className="project-detail__title">{project.name}</h1>
          <p className="project-detail__meta">
            <span className="project-detail__meta-item">ID: {project.id.slice(0, 8)}...</span>
            <span className="project-detail__meta-item">•</span>
            <span className="project-detail__meta-item">
              Created {formatDate(project.created_at)}
            </span>
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setShowTaskModal(true)}
          aria-label="Create new task"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          Add Task
        </button>
      </header>

      <section className="project-detail__overview">
        <h2 className="project-detail__section-title">Overview</h2>
        <div className="project-detail__content">
          <p className="project-detail__description">
            {project.description || "No description provided"}
          </p>
          <div className="project-detail__info-grid">
            <div className="project-detail__info-item">
              <h3 className="project-detail__info-label">AI Provider</h3>
              <p className="project-detail__info-value">
                {project.ai_provider || "Not specified"}
              </p>
            </div>
            <div className="project-detail__info-item">
              <h3 className="project-detail__info-label">Language</h3>
              <p className="project-detail__info-value">
                {project.preferred_language}
              </p>
            </div>
            <div className="project-detail__info-item">
              <h3 className="project-detail__info-label">Timezone</h3>
              <p className="project-detail__info-value">
                {project.timezone}
              </p>
            </div>
            <div className="project-detail__info-item">
              <h3 className="project-detail__info-label">Telegram</h3>
              <p className="project-detail__info-value">
                {project.telegram_notifications_enabled
                  ? "Enabled"
                  : "Disabled"}
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="project-detail__tasks">
        <h2 className="project-detail__section-title">
          Tasks ({tasks.length})
          <button
            className="btn btn-outline btn-sm"
            onClick={() => setShowTaskModal(true)}
          >
            + New Task
          </button>
        </h2>

        {tasks.length > 0 ? (
          <TaskList
            projectId={projectId}
            tasks={tasks}
            onTaskUpdate={handleTaskUpdate}
          />
        ) : (
          <div className="empty-state">
            <h3 className="empty-state__title">No Tasks Yet</h3>
            <p className="empty-state__description">
              Create your first task to start building with this project.
            </p>
          </div>
        )}
      </section>

      {/* Task Creation Modal */}
      {showTaskModal && (
        <div className="modal-overlay" onClick={() => setShowTaskModal(false)} role="dialog" aria-modal="true" aria-labelledby="create-task-title">
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <header className="modal__header">
              <h2 id="create-task-title" className="modal__title">
                Create New Task
              </h2>
              <button className="modal__close" onClick={() => setShowTaskModal(false)} aria-label="Close">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </header>
            <ProjectTaskForm
              projectId={projectId}
              initialData={taskFormData}
              onSubmit={handleTaskCreate}
              onCancel={() => setShowTaskModal(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectDetail;