import React, { useState } from "react";
import ProjectList from "./components/ProjectList";
import Loading from "./components/Loading";
import "./App.css";

const App: React.FC = () => {
  const [showLoading, setShowLoading] = useState(true);

  return (
    <div className="min-h-screen bg-gray-50 text-gray-800">
      <header className="bg-white shadow-sm py-4">
        <div className="container mx-auto px-4">
          <h1 className="text-3xl font-bold text-gray-800">NexusForge — Autonomous Software Development</h1>
          <p className="text-gray-600">Build AI-powered tools, automate workflows, and create smart solutions</p>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {showLoading ? (
          <Loading message="Initializing NexusForge..." />
        ) : (
          <ProjectList />
        )}
      </main>

      <footer className="bg-white py-8">
        <div className="container mx-auto px-4">
          <p className="text-gray-600 text-center">© 2026 NexusForge. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default App;