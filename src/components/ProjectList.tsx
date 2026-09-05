import React, { useState, useEffect } from "react";
import { Project, HealthResponse } from "../types";
import axios from "axios";

const API_BASE = "http://localhost:8000/api";

const ProjectList: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        // Health check first
        const healthRes = await axios.get<HealthResponse>(`${API_BASE}/health`);
        console.log("Health check:", healthRes.data);
        
        // Then get projects
        const res = await axios.get<Project[]>(`${API_BASE}/projects`);
        setProjects(res.data);
      } catch (err) {
        setError("Failed to fetch projects");
        console.error("API error:", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchProjects();
  }, []);

  if (loading) {
    return <div className="p-6">Loading...</div>;
  }

  if (error) {
    return <div className="p-6 text-red-500">{error}</div>;
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-800">NexusForge Projects</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {projects.map((project) => (
          <div key={project.id} className="border border-gray-200 rounded-lg p-4 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-700">{project.name}</h2>
            <p className="text-gray-600 text-sm">{project.description || "No description"}</p>
            <div className="mt-2 text-sm text-gray-500">
              Owner: {project.owner_id || "N/A"}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProjectList;