import React, { useState, useEffect } from "react";
import { agentApi, settingsApi } from "../services/api";
import { useLanguage } from "../context/LanguageContext";
import Loading from "../components/Loading";
import "./AgentsPage.css";

interface AgentConfig {
  id: string;
  role: string;
  name: string;
  codename?: string;
  codename_fa?: string;
  avatar_badge?: string;
  description: string;
  system_prompt: string;
  provider: string;
  model: string;
  reasoning_effort: string;
  temperature: number;
  max_tokens: number;
  skills: string[];
  is_active: boolean;
  is_builtin: boolean;
  created_at: string;
  updated_at: string;
}

const PROVIDERS = [
  { id: "openrouter", name: "OpenRouter (Recommended / Free & Fast)" },
  { id: "anthropic", name: "Anthropic Claude" },
  { id: "openai", name: "OpenAI" },
  { id: "google", name: "Google Gemini" },
  { id: "ollama", name: "Ollama (Local)" },
  { id: "groq", name: "Groq (Fast LPU)" },
  { id: "deepseek", name: "DeepSeek" },
];

const AgentsPage: React.FC = () => {
  const { language } = useLanguage();
  const [agents, setAgents] = useState<AgentConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "active" | "custom">("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Edit / Create Modal State
  const [selectedAgent, setSelectedAgent] = useState<AgentConfig | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  // Form State
  const [formData, setFormData] = useState({
    name: "",
    role: "",
    description: "",
    system_prompt: "",
    provider: "anthropic",
    model: "claude-3-5-sonnet-20241022",
    reasoning_effort: "medium",
    temperature: 0.7,
    max_tokens: 4000,
    skills: "",
    is_active: true,
  });

  // Available models dynamically fetched
  const [availableModels, setAvailableModels] = useState<Array<{ id: string; name: string; supports_reasoning: boolean }>>([]);
  const [fetchingModels, setFetchingModels] = useState(false);

  const fetchAgents = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await agentApi.getAll();
      setAgents(data);
    } catch (err: any) {
      setError(err?.detail || "Failed to load agents configuration");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  const loadModelsForProvider = async (provider: string) => {
    try {
      setFetchingModels(true);
      const res = await settingsApi.fetchModels({ provider });
      setAvailableModels(res.models || []);
    } catch (e) {
      // Fallback
      setAvailableModels([]);
    } finally {
      setFetchingModels(false);
    }
  };

  const openEditModal = (agent: AgentConfig) => {
    setIsCreating(false);
    setSelectedAgent(agent);
    setFormData({
      name: agent.name,
      role: agent.role,
      description: agent.description,
      system_prompt: agent.system_prompt,
      provider: agent.provider,
      model: agent.model,
      reasoning_effort: agent.reasoning_effort || "medium",
      temperature: agent.temperature ?? 0.7,
      max_tokens: agent.max_tokens || 4000,
      skills: (agent.skills || []).join(", "),
      is_active: agent.is_active,
    });
    loadModelsForProvider(agent.provider);
    setSaveSuccess(null);
    setModalOpen(true);
  };

  const openCreateModal = () => {
    setIsCreating(true);
    setSelectedAgent(null);
    setFormData({
      name: "",
      role: "",
      description: "",
      system_prompt: "You are an autonomous specialist agent in NexusForge. Assist the team with high precision and thorough execution.",
      provider: "anthropic",
      model: "claude-3-5-sonnet-20241022",
      reasoning_effort: "medium",
      temperature: 0.7,
      max_tokens: 4000,
      skills: "analysis, coding",
      is_active: true,
    });
    loadModelsForProvider("anthropic");
    setSaveSuccess(null);
    setModalOpen(true);
  };

  const handleProviderChange = (newProvider: string) => {
    setFormData((prev) => ({ ...prev, provider: newProvider }));
    loadModelsForProvider(newProvider);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError(null);
      const skillsArray = formData.skills
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      const payload = {
        name: formData.name,
        role: formData.role,
        description: formData.description,
        system_prompt: formData.system_prompt,
        provider: formData.provider,
        model: formData.model,
        reasoning_effort: formData.reasoning_effort,
        temperature: Number(formData.temperature),
        max_tokens: Number(formData.max_tokens),
        skills: skillsArray,
        is_active: formData.is_active,
      };

      if (isCreating) {
        await agentApi.create(payload);
        setSaveSuccess("New agent created successfully!");
      } else if (selectedAgent) {
        await agentApi.update(selectedAgent.id, payload);
        setSaveSuccess(`Agent '${formData.name}' updated successfully!`);
      }

      await fetchAgents();
      setTimeout(() => {
        setModalOpen(false);
        setSaveSuccess(null);
      }, 1000);
    } catch (err: any) {
      setError(err?.detail || "Failed to save agent configuration");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (agent: AgentConfig) => {
    if (!window.confirm(`Are you sure you want to delete the agent '${agent.name}'?`)) {
      return;
    }
    try {
      await agentApi.delete(agent.id);
      fetchAgents();
    } catch (err: any) {
      alert(err?.detail || "Failed to delete agent");
    }
  };

  const handleToggleActive = async (agent: AgentConfig) => {
    try {
      await agentApi.update(agent.id, { is_active: !agent.is_active });
      setAgents((prev) =>
        prev.map((a) => (a.id === agent.id ? { ...a, is_active: !a.is_active } : a))
      );
    } catch (err: any) {
      alert("Failed to update status");
    }
  };

  const handleReset = async () => {
    if (!window.confirm("Reset all agents and prompts to factory defaults? Any custom prompt edits will be restored.")) {
      return;
    }
    try {
      setLoading(true);
      await agentApi.reset();
      await fetchAgents();
    } catch (err: any) {
      setError(err?.detail || "Failed to reset agents");
    } finally {
      setLoading(false);
    }
  };

  const filteredAgents = agents.filter((a) => {
    if (filter === "active" && !a.is_active) return false;
    if (filter === "custom" && a.is_builtin) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const inName = a.name.toLowerCase().includes(q);
      const inRole = a.role.toLowerCase().includes(q);
      const inDesc = a.description.toLowerCase().includes(q);
      const inSkill = (a.skills || []).some((s) => s.toLowerCase().includes(q));
      const inCodename = (a.codename || "").toLowerCase().includes(q) || (a.codename_fa || "").toLowerCase().includes(q);
      return inName || inRole || inDesc || inSkill || inCodename;
    }
    return true;
  });

  const activeCount = agents.filter((a) => a.is_active).length;
  const customCount = agents.filter((a) => !a.is_builtin).length;

  return (
    <div className="agents-page">
      {/* Header */}
      <header className="agents-page__header">
        <div>
          <div className="agents-page__badge">
            {language === "fa" ? "معماری تیم چند ایجنتی هوش مصنوعی" : "AI Multi-Agent Team Architecture"}
          </div>
          <h1 className="agents-page__title">
            {language === "fa" ? "مدیریت ایجنت‌های هوشمند و پرامپت‌ها" : "Autonomous Agents & Prompt Customization"}
          </h1>
          <p className="agents-page__desc">
            {language === "fa"
              ? "پرامپت‌های سیستمی را ویرایش کنید، مدل مناسب هر نقش را تخصیص دهید، میزان استدلال (Reasoning) را تعیین کرده و تیم هوشمند خود را مدیریت کنید."
              : "Tailor system prompts, adjust AI models, set reasoning intensity, and customize the specialist agents in your workspace."}
          </p>
        </div>
        <div className="agents-page__header-actions">
          <button className="btn btn--outline" onClick={handleReset} title={language === "fa" ? "بازنشانی همه به پیش‌فرض کارخانه" : "Reset all prompts to factory defaults"}>
            ↺ {language === "fa" ? "بازنشانی پیش‌فرض‌ها" : "Reset Defaults"}
          </button>
          <button className="btn btn--primary" onClick={openCreateModal}>
            + {language === "fa" ? "تعریف ایجنت جدید" : "Create New Agent"}
          </button>
        </div>
      </header>

      {/* Stats and Filter Bar */}
      <div className="agents-toolbar">
        <div className="agents-stats">
          <span className="stat-pill">
            {language === "fa" ? "کل ایجنت‌ها:" : "Total Agents:"} <strong>{agents.length}</strong>
          </span>
          <span className="stat-pill stat-pill--active">
            {language === "fa" ? "فعال:" : "Active:"} <strong>{activeCount}</strong>
          </span>
          {customCount > 0 && (
            <span className="stat-pill stat-pill--custom">
              {language === "fa" ? "نقش‌های سفارشی:" : "Custom Roles:"} <strong>{customCount}</strong>
            </span>
          )}
        </div>

        <div className="agents-controls">
          <div className="search-box">
            <input
              type="text"
              placeholder={language === "fa" ? "جستجوی ایجنت، نام مستعار، نقش یا مهارت..." : "Search agent, codename, role, skill..."}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
          </div>

          <div className="filter-tabs">
            <button
              className={`filter-tab ${filter === "all" ? "active" : ""}`}
              onClick={() => setFilter("all")}
            >
              {language === "fa" ? "همه" : "All"} ({agents.length})
            </button>
            <button
              className={`filter-tab ${filter === "active" ? "active" : ""}`}
              onClick={() => setFilter("active")}
            >
              {language === "fa" ? "فعال" : "Active"} ({activeCount})
            </button>
            <button
              className={`filter-tab ${filter === "custom" ? "active" : ""}`}
              onClick={() => setFilter("custom")}
            >
              {language === "fa" ? "سفارشی" : "Custom"} ({customCount})
            </button>
          </div>
        </div>
      </div>

      {error && <div className="alert alert--error">{error}</div>}

      {/* Agents Grid */}
      {loading ? (
        <Loading message={language === "fa" ? "در حال بارگذاری معماری ایجنت‌های هوشمند..." : "Loading autonomous agent configurations..."} />
      ) : (
        <div className="agents-grid">
          {filteredAgents.map((agent) => (
            <div
              key={agent.id}
              className={`agent-card ${agent.is_active ? "agent-card--active" : "agent-card--inactive"}`}
            >
              <div className="agent-card__header">
                <div className="agent-card__avatar">
                  {agent.avatar_badge || agent.name.charAt(0).toUpperCase()}
                </div>
                <div className="agent-card__title-wrap">
                  <div className="agent-card__name-row">
                    <h3 className="agent-card__name">{agent.name}</h3>
                    {agent.is_builtin ? (
                      <span className="tag tag--builtin">{language === "fa" ? "هسته اصلی" : "Core"}</span>
                    ) : (
                      <span className="tag tag--custom">{language === "fa" ? "سفارشی" : "Custom"}</span>
                    )}
                    {agent.role === "chief_orchestrator" && (
                      <span className="tag tag--orchestrator">
                        👑 {language === "fa" ? "فرمانده کل (تنها دریافت‌کننده تسک)" : "Chief Orchestrator"}
                      </span>
                    )}
                  </div>
                  {(agent.codename || agent.codename_fa) && (
                    <div className="agent-card__codename-badge">
                      ⚡ {language === "fa" && agent.codename_fa ? agent.codename_fa : agent.codename}
                    </div>
                  )}
                  <span className="agent-card__role">role: {agent.role}</span>
                </div>
                <button
                  className={`toggle-btn ${agent.is_active ? "toggle-btn--on" : "toggle-btn--off"}`}
                  onClick={() => handleToggleActive(agent)}
                  title={agent.is_active ? "Disable Agent" : "Enable Agent"}
                >
                  {agent.is_active ? (language === "fa" ? "فعال" : "Active") : (language === "fa" ? "غیرفعال" : "Disabled")}
                </button>
              </div>

              <p className="agent-card__desc">{agent.description}</p>

              {/* Model & Reasoning Info */}
              <div className="agent-card__specs">
                <div className="spec-item">
                  <span className="spec-label">{language === "fa" ? "سرویس‌دهنده" : "Provider"}</span>
                  <span className="spec-val spec-val--provider">{agent.provider.toUpperCase()}</span>
                </div>
                <div className="spec-item">
                  <span className="spec-label">{language === "fa" ? "مدل هوش مصنوعی" : "Model"}</span>
                  <span className="spec-val spec-val--model" title={agent.model}>
                    {agent.model}
                  </span>
                </div>
                <div className="spec-item">
                  <span className="spec-label">{language === "fa" ? "سطح استدلال" : "Reasoning"}</span>
                  <span className={`spec-val spec-val--reasoning reasoning--${agent.reasoning_effort || "none"}`}>
                    {(agent.reasoning_effort || "none").toUpperCase()}
                  </span>
                </div>
              </div>

              {/* Skills Tags */}
              {agent.skills && agent.skills.length > 0 && (
                <div className="agent-card__skills">
                  {agent.skills.map((skill, idx) => (
                    <span key={idx} className="skill-chip">
                      #{skill}
                    </span>
                  ))}
                </div>
              )}

              {/* Detailed System Prompt Accordion */}
              <details className="agent-prompt-accordion">
                <summary className="agent-prompt-summary">
                  <span className="agent-prompt-title">📜 {language === "fa" ? "مشاهده پرامپت تخصصی و جزئیات کامل" : "View Detailed System Prompt"}</span>
                  <span className="agent-prompt-len">({agent.system_prompt?.length || 0} {language === "fa" ? "کاراکتر" : "chars"})</span>
                </summary>
                <div className="agent-prompt-body">
                  <pre>{agent.system_prompt}</pre>
                </div>
              </details>

              {/* Card Footer Actions */}
              <div className="agent-card__footer">
                <button
                  className="btn btn--card-edit"
                  onClick={() => openEditModal(agent)}
                >
                  ✎ {language === "fa" ? "شخصی‌سازی پرامپت و مدل" : "Customize Prompt & Config"}
                </button>
                {!agent.is_builtin && (
                  <button
                    className="btn btn--card-delete"
                    onClick={() => handleDelete(agent)}
                    title={language === "fa" ? "حذف ایجنت" : "Delete Agent"}
                  >
                    🗑
                  </button>
                )}
              </div>
            </div>
          ))}

          {filteredAgents.length === 0 && (
            <div className="empty-agents">
              <h3>{language === "fa" ? "هیچ ایجنتی یافت نشد" : "No agents found"}</h3>
              <p>{language === "fa" ? "فیلتر جستجو را تغییر دهید یا ایجنت جدیدی تعریف نمایید." : "Try modifying your search filter or add a new specialized agent."}</p>
              <button className="btn btn--primary" onClick={openCreateModal}>
                + {language === "fa" ? "تعریف ایجنت جدید" : "Create Agent"}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Edit / Create Agent Modal */}
      {modalOpen && (
        <div className="modal-backdrop">
          <div className="modal modal--agent">
            <div className="modal__header">
              <div>
                <h2>{isCreating ? "Create Specialized Agent" : `Edit Agent: ${formData.name}`}</h2>
                <p className="modal__subtitle">
                  Customize the system prompt, AI provider, reasoning tokens, and execution constraints.
                </p>
              </div>
              <button className="modal__close" onClick={() => setModalOpen(false)}>
                ✕
              </button>
            </div>

            {saveSuccess && <div className="alert alert--success">{saveSuccess}</div>}

            <form onSubmit={handleSave} className="modal__form">
              <div className="form-row">
                <div className="form-group flex-1">
                  <label className="form-label">Agent Name *</label>
                  <input
                    type="text"
                    required
                    className="form-input"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g. Lead Security Auditor"
                  />
                </div>
                <div className="form-group flex-1">
                  <label className="form-label">Role Identifier *</label>
                  <input
                    type="text"
                    required
                    disabled={!isCreating}
                    className="form-input"
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    placeholder="e.g. security_auditor"
                  />
                  {!isCreating && <span className="field-hint">Built-in role identifier cannot be changed.</span>}
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Short Description *</label>
                <input
                  type="text"
                  required
                  className="form-input"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Primary objective and responsibilities of this agent profile"
                />
              </div>

              {/* Provider & Model Selectors */}
              <div className="form-row form-row--specs">
                <div className="form-group flex-1">
                  <label className="form-label">AI Provider</label>
                  <select
                    className="form-select"
                    value={formData.provider}
                    onChange={(e) => handleProviderChange(e.target.value)}
                  >
                    {PROVIDERS.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group flex-1">
                  <label className="form-label">
                    Model {fetchingModels && <span className="spinner-text">(Fetching...)</span>}
                  </label>
                  {availableModels.length > 0 ? (
                    <select
                      className="form-select"
                      value={formData.model}
                      onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                    >
                      {availableModels.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.name} {m.supports_reasoning ? "🧠 [Reasoning]" : ""}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="text"
                      className="form-input"
                      value={formData.model}
                      onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                      placeholder="e.g. claude-3-5-sonnet-20241022"
                    />
                  )}
                </div>

                <div className="form-group flex-1">
                  <label className="form-label">Reasoning Effort</label>
                  <select
                    className="form-select"
                    value={formData.reasoning_effort}
                    onChange={(e) => setFormData({ ...formData, reasoning_effort: e.target.value })}
                  >
                    <option value="none">None (Fastest)</option>
                    <option value="low">Low (Light Thinking)</option>
                    <option value="medium">Medium (Standard)</option>
                    <option value="high">High (Deep Planning & Code)</option>
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group flex-1">
                  <label className="form-label">Temperature: {formData.temperature}</label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    className="form-range"
                    value={formData.temperature}
                    onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
                  />
                  <span className="field-hint">Lower = deterministic code; Higher = creative ideation.</span>
                </div>

                <div className="form-group flex-1">
                  <label className="form-label">Max Token Output</label>
                  <input
                    type="number"
                    min="500"
                    max="64000"
                    step="500"
                    className="form-input"
                    value={formData.max_tokens}
                    onChange={(e) => setFormData({ ...formData, max_tokens: parseInt(e.target.value) })}
                  />
                </div>
              </div>

              {/* System Prompt Textarea */}
              <div className="form-group">
                <div className="prompt-header">
                  <label className="form-label">Agent System Prompt (Instructions) *</label>
                  <div className="prompt-tags">
                    <span className="tag-hint">Variables:</span>
                    <code>&#123;&#123;project_name&#125;&#125;</code>
                    <code>&#123;&#123;task_description&#125;&#125;</code>
                  </div>
                </div>
                <textarea
                  rows={8}
                  required
                  className="form-textarea form-textarea--prompt"
                  value={formData.system_prompt}
                  onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                  placeholder="Define role behavioral guidelines, coding principles, tool usage criteria, and acceptance requirements..."
                />
              </div>

              <div className="form-group">
                <label className="form-label">Skills & Capabilities (comma-separated)</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.skills}
                  onChange={(e) => setFormData({ ...formData, skills: e.target.value })}
                  placeholder="e.g. security_audit, penetration_testing, owasp, code_review"
                />
              </div>

              <div className="form-checkbox-row">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                  <span>Enable this agent for autonomous project task assignment</span>
                </label>
              </div>

              <div className="modal__actions">
                <button
                  type="button"
                  className="btn btn--outline"
                  onClick={() => setModalOpen(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="btn btn--primary"
                >
                  {saving ? "Saving..." : isCreating ? "Create Agent" : "Save Changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentsPage;
