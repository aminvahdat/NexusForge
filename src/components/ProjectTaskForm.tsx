import React, { useState } from "react";
import { TaskCreate, AgentRole, Priority, TaskStatus } from "../types";
import "./TaskForm.css";

interface TaskFormProps {
  projectId: string;
  initialData?: TaskCreate;
  onSubmit: (data: TaskCreate) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
  error?: string | null;
}

// Agent role options from backend enum
const agentRoles = Object.entries(AgentRole).map(([key, value]) => ({
  label: key.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()),
  value: value,
  description: getRoleDescription(key)
}));

function getRoleDescription(role: string): string {
  const descriptions: Record<string, string> = {
    CHIEF_ORCHESTRATOR: "Orchestrates overall task execution",
    PROJECT_PLANNER: "Breaks down projects into actionable tasks",
    SOFTWARE_ARCHITECT: "Designs system architecture and patterns",
    RESEARCH_AGENT: "Researches topics and gathers information",
    UI_UX_AGENT: "Designs user interfaces and experiences",
    FRONTEND_AGENT: "Implements frontend components and UI",
    BACKEND_AGENT: "Builds server-side logic and APIs",
    MOBILE_AGENT: "Develops mobile applications",
    DATABASE_AGENT: "Manages database design and queries",
    SECURITY_AGENT: "Audits security and finds vulnerabilities",
    QA_AGENT: "Tests and verifies functionality",
    DEVOPS_AGENT: "Handles deployment and infrastructure",
  };
  return descriptions[role] || "";
}

const TaskForm: React.FC<TaskFormProps> = ({
  projectId,
  initialData,
  onSubmit,
  onCancel,
  loading = false,
  error = null,
}) => {
  const [formData, setFormData] = useState<TaskCreate>(
    initialData || {
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
    }
  );

  const handleChange = (field: keyof TaskCreate, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleStringListChange = (field: keyof TaskCreate, value: string) => {
    const items = value
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
    handleChange(field, items.length > 0 ? items : null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title.trim() || !formData.description.trim()) {
      return;
    }
    // Ensure project_id is set
    const submission: TaskCreate = { ...formData, project_id: projectId };
    await onSubmit(submission);
  };

  return (
    <form onSubmit={handleSubmit} className="task-form modal__body" noValidate>
      {error && (
        <div className="alert alert-error" role="alert">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
          <span>{error}</span>
        </div>
      )}

      <div className="form-group">
        <label htmlFor="task-title" className="label">Task Title *</label>
        <input
          type="text"
          id="task-title"
          className="input"
          value={formData.title}
          onChange={(e) => handleChange("title", e.target.value)}
          required
          placeholder="What needs to be done?"
          maxLength={500}
        />
      </div>

      <div className="form-group">
        <label htmlFor="task-description" className="label">Description *</label>
        <textarea
          id="task-description"
          className="input textarea"
          value={formData.description}
          onChange={(e) => handleChange("description", e.target.value)}
          required
          placeholder="Detailed description of the task..."
          rows={4}
        />
      </div>

      <div className="form-group">
        <label htmlFor="task-role" className="label">Agent Role</label>
        <select
          id="task-role"
          className="input select"
          value={formData.role}
          onChange={(e) => handleChange("role", e.target.value)}
        >
          {agentRoles.map((role) => (
            <option key={role.value} value={role.value}>
              {role.label}
            </option>
          ))}
        </select>
        <p className="form-helper-text">
          Agent roles are logical profiles — selecting a role assigns a specific
          task type, not a permanent worker. The worker pool manages execution.
        </p>
      </div>

      <div className="form-group">
        <label htmlFor="task-priority" className="label">Priority</label>
        <select
          id="task-priority"
          className="input select"
          value={formData.priority}
          onChange={(e) => handleChange("priority", e.target.value)}
        >
          <option value={Priority.LOW}>Low</option>
          <option value={Priority.MEDIUM}>Medium</option>
          <option value={Priority.HIGH}>High</option>
          <option value={Priority.CRITICAL}>Critical</option>
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="task-required-skills" className="label">Required Skills</label>
        <input
          type="text"
          id="task-required-skills"
          className="input"
          value={(formData.required_skills || []).join(", ")}
          onChange={(e) => handleStringListChange("required_skills", e.target.value)}
          placeholder="e.g., react, typescript, postgresql"
        />
        <p className="form-helper-text">Comma-separated list of required skills</p>
      </div>

      <div className="form-group">
        <label htmlFor="task-due-date" className="label">Due Date</label>
        <input
          type="date"
          id="task-due-date"
          className="input"
          value={formData.due_date ? new Date(formData.due_date).toISOString().split("T")[0] : ""}
          onChange={(e) => handleChange("due_date", e.target.value || null)}
        />
      </div>

      <div className="form-group">
        <label htmlFor="task-max-retries" className="label">Max Retries</label>
        <input
          type="number"
          id="task-max-retries"
          className="input"
          type="number"
          min="0"
          max="10"
          value={formData.max_retries}
          onChange={(e) => handleChange("max_retries", parseInt(e.target.value, 10))}
        />
      </div>

      <div className="form-group">
        <label htmlFor="task-acceptance-criteria" className="label">Acceptance Criteria</label>
        <textarea
          id="task-acceptance-criteria"
          className="input textarea"
          value={(formData.acceptance_criteria || []).join("\n")}
          onChange={(e) => handleStringListChange("acceptance_criteria", e.target.value)}
          placeholder="One criterion per line"
          rows={3}
        />
      </div>

      <footer className="modal__footer">
        <button
          type="button"
          className="btn btn-secondary"
          onClick={onCancel}
          disabled={loading}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading || !formData.title.trim() || !formData.description.trim()}
        >
          {loading ? (
            <>
              <span className="loading-spinner" style={{ width: "16px", height: "16px" }}></span>
              Creating...
            </>
          ) : (
            "Create Task"
          )}
        </button>
      </footer>
    </form>
  );
};

export default TaskForm;