import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useLanguage } from "../context/LanguageContext";
import { settingsApi } from "../services/api";
import "./Settings.css";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

interface RoleRecommendation {
  role: string;
  agent_name: string;
  codename: string;
  codename_fa?: string;
  recommended_model: string;
  recommended_effort: string;
  reason: string;
}

interface APIKeyItem {
  id: string;
  name: string;
  provider: string;
  masked_key: string;
  model: string | null;
  max_tokens: number | null;
  is_active: boolean;
  created_at: string;
  last_used: string | null;
}

interface SystemConfig {
  default_provider: string;
  default_model: string;
  ollama_base_url: string;
  telegram_notifications: boolean;
  telegram_bot_token: string | null;
  telegram_chat_id: string | null;
  preferred_language: string;
  max_workers: number;
}

const PROVIDERS = [
  {
    id: "openrouter",
    name: "OpenRouter",
    tagline: "Universal access to 400+ models (Claude, OpenAI, DeepSeek, Google, Meta, Mistral)",
    badge: "Universal Hub",
    badgeColor: "#6366F1",
    defaultModel: "",
    models: [],
    keyPlaceholder: "sk-or-v1-...",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="2" y1="12" x2="22" y2="12"></line>
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
      </svg>
    ),
  },
  {
    id: "anthropic",
    name: "Anthropic Claude",
    tagline: "Claude 3.7 Sonnet (Hybrid Reasoning) & 3.5 Sonnet",
    badge: "Best for Coding",
    badgeColor: "#8B5CF6",
    defaultModel: "claude-3-7-sonnet-latest",
    models: ["claude-3-7-sonnet-latest", "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
    keyPlaceholder: "sk-ant-...",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
        <polyline points="2 17 12 22 22 17"></polyline>
        <polyline points="2 12 12 17 22 12"></polyline>
      </svg>
    ),
  },
  {
    id: "openai",
    name: "OpenAI",
    tagline: "o3-mini, o1 Reasoning & GPT-4o Flagship",
    badge: "Recommended",
    badgeColor: "#007BFF",
    defaultModel: "o3-mini",
    models: ["o3-mini", "o1", "o1-mini", "gpt-4o", "gpt-4o-mini"],
    keyPlaceholder: "sk-proj-...",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 2a10 10 0 0 1 10 10c0 5.523-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2z"></path>
        <path d="M12 6v6l4 2"></path>
      </svg>
    ),
  },
  {
    id: "deepseek",
    name: "DeepSeek",
    tagline: "DeepSeek-R1 full reasoning & DeepSeek-V3 fast chat",
    badge: "Reasoning King",
    badgeColor: "#0EA5E9",
    defaultModel: "deepseek-reasoner",
    models: ["deepseek-reasoner", "deepseek-chat"],
    keyPlaceholder: "sk-...",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10"></circle>
        <path d="M12 16v-4"></path>
        <path d="M12 8h.01"></path>
      </svg>
    ),
  },
  {
    id: "google",
    name: "Google Gemini",
    tagline: "Gemini 2.5 Pro (Thinking) & Gemini 2.0 Flash",
    badge: "2M Context",
    badgeColor: "#10B981",
    defaultModel: "gemini-2.0-flash",
    models: ["gemini-2.5-pro", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
    keyPlaceholder: "AIzaSy...",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"></path>
      </svg>
    ),
  },
  {
    id: "ollama",
    name: "Ollama (Local / Offline)",
    tagline: "Run DeepSeek-R1, Llama 3.3 & Qwen on your GPU",
    badge: "100% Private",
    badgeColor: "#F59E0B",
    defaultModel: "deepseek-r1:8b",
    models: ["deepseek-r1:8b", "llama3.3:70b", "llama3.1:8b", "qwen2.5-coder:7b", "mistral:7b"],
    keyPlaceholder: "ollama-local (no key required)",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="2" y="2" width="20" height="8" rx="2"></rect>
        <rect x="2" y="14" width="20" height="8" rx="2"></rect>
        <line x1="6" y1="6" x2="6.01" y2="6"></line>
        <line x1="6" y1="18" x2="6.01" y2="18"></line>
      </svg>
    ),
  },
  {
    id: "groq",
    name: "Groq / Fast LPU",
    tagline: "Ultra high-speed DeepSeek-R1 Distill & Llama 3.3 at 500 tok/s",
    badge: "Ultra Fast",
    badgeColor: "#EC4899",
    defaultModel: "deepseek-r1-distill-llama-70b",
    models: ["deepseek-r1-distill-llama-70b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
    keyPlaceholder: "gsk_...",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
      </svg>
    ),
  },
];

const Settings: React.FC = () => {
  const navigate = useNavigate();
  const { language } = useLanguage();
  const [activeTab, setActiveTab] = useState<"api" | "system" | "preferences">("api");
  const [apiKeys, setApiKeys] = useState<APIKeyItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Active form state
  const [selectedProvider, setSelectedProvider] = useState(PROVIDERS[0]);
  const [keyName, setKeyName] = useState("OpenAI Primary");
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [selectedModel, setSelectedModel] = useState(PROVIDERS[0].defaultModel);
  const [maxTokens, setMaxTokens] = useState(4000);
  const [reasoningEffort, setReasoningEffort] = useState("medium");
  const [temperature, setTemperature] = useState(0.7);
  const [customBaseUrl, setCustomBaseUrl] = useState("");
  const [isCustomModel, setIsCustomModel] = useState(false);
  const [customModelInput, setCustomModelInput] = useState("");
  const [dynamicModels, setDynamicModels] = useState<Array<{ id: string; name: string; supports_reasoning: boolean }>>([]);
  const [fetchingModels, setFetchingModels] = useState(false);
  const [showKey, setShowKey] = useState(false);
  const [savingKey, setSavingKey] = useState(false);
  const [testingKey, setTestingKey] = useState(false);

  // Smart Role Recommendations State
  const [recommendations, setRecommendations] = useState<RoleRecommendation[]>([]);
  const [fetchingRecommendations, setFetchingRecommendations] = useState(false);
  const [applyingRecommendations, setApplyingRecommendations] = useState(false);

  // System config state
  const [systemConfig, setSystemConfig] = useState<SystemConfig>({
    default_provider: "openai",
    default_model: "gpt-4o",
    ollama_base_url: "http://localhost:11434",
    telegram_notifications: false,
    telegram_bot_token: "",
    telegram_chat_id: "",
    preferred_language: "en",
    max_workers: 2,
  });
  const [savingSystem, setSavingSystem] = useState(false);

  // Notifications / feedback
  const [toast, setToast] = useState<{ type: "success" | "error" | "info"; message: string } | null>(null);

  const showToast = (type: "success" | "error" | "info", message: string) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 4000);
  };

  const getAuthHeaders = () => {
    const token = localStorage.getItem("token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const [keysRes, sysRes] = await Promise.all([
        axios.get(`${API_BASE}/settings/keys`, { headers: getAuthHeaders() }),
        axios.get(`${API_BASE}/settings/system`, { headers: getAuthHeaders() }),
      ]);
      setApiKeys(keysRes.data);
      if (sysRes.data) {
        setSystemConfig(sysRes.data);
      }
    } catch (err) {
      console.warn("Failed to load settings:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSelectProvider = (prov: typeof PROVIDERS[0]) => {
    setSelectedProvider(prov);
    setKeyName(`${prov.name} Key`);
    setSelectedModel(prov.defaultModel);
    setApiKeyInput("");
    setShowKey(false);
    setIsCustomModel(false);
    setCustomModelInput("");
    setDynamicModels([]);
    setRecommendations([]);
    if (prov.id === "ollama") {
      setCustomBaseUrl(systemConfig.ollama_base_url || "http://localhost:11434");
    } else {
      setCustomBaseUrl("");
    }
  };

  const handleFetchModels = async () => {
    setFetchingModels(true);
    try {
      const res = await axios.post(
        `${API_BASE}/settings/fetch-models`,
        {
          provider: selectedProvider.id,
          api_key: apiKeyInput.trim() || undefined,
          base_url: customBaseUrl.trim() || (selectedProvider.id === "ollama" ? systemConfig.ollama_base_url : undefined),
        },
        { headers: getAuthHeaders() }
      );
      if (res.data.models && res.data.models.length > 0) {
        setDynamicModels(res.data.models);
        setSelectedModel(res.data.models[0].id);
        showToast("success", `Fetched ${res.data.models.length} available models for ${selectedProvider.name} (${res.data.source})`);
        // Automatically fetch role recommendations for fetched models
        handleGetRecommendations();
      }
    } catch (err: any) {
      showToast("error", err.response?.data?.detail || "Failed to fetch models");
    } finally {
      setFetchingModels(false);
    }
  };

  const handleGetRecommendations = async () => {
    setFetchingRecommendations(true);
    try {
      const res = await settingsApi.recommendRoles({
        provider: selectedProvider.id,
        api_key: apiKeyInput.trim() || undefined,
        base_url: customBaseUrl.trim() || (selectedProvider.id === "ollama" ? systemConfig.ollama_base_url : undefined),
      });
      if (res.recommendations && res.recommendations.length > 0) {
        setRecommendations(res.recommendations);
        showToast(
          "success",
          language === "fa"
            ? `پیشنهادات هوشمند برای ${res.recommendations.length} نقش از مدل‌های ${selectedProvider.name} استخراج شد!`
            : `Generated recommendations for ${res.recommendations.length} roles from ${selectedProvider.name}`
        );
      }
    } catch (err: any) {
      showToast("error", err.response?.data?.detail || "Failed to generate recommendations");
    } finally {
      setFetchingRecommendations(false);
    }
  };

  const handleApplyRecommendations = async () => {
    if (recommendations.length === 0) return;
    setApplyingRecommendations(true);
    try {
      const res = await settingsApi.applyRecommendations({
        provider: selectedProvider.id,
        recommendations,
      });
      showToast(
        "success",
        language === "fa"
          ? `مدل‌های پیشنهادی با موفقیت به تمام ${res.updated_agents || recommendations.length} ایجنت اعمال شد!`
          : `Successfully applied recommendations to all ${res.updated_agents || recommendations.length} agents!`
      );
    } catch (err: any) {
      showToast("error", err.response?.data?.detail || "Failed to apply recommendations");
    } finally {
      setApplyingRecommendations(false);
    }
  };

  const handleTestKey = async () => {
    if (!apiKeyInput.trim() && selectedProvider.id !== "ollama") {
      showToast("error", "Please enter an API Key to test");
      return;
    }
    setTestingKey(true);
    try {
      const res = await axios.post(
        `${API_BASE}/settings/test-key`,
        {
          provider: selectedProvider.id,
          api_key: apiKeyInput || "ollama-local",
          base_url: customBaseUrl || (selectedProvider.id === "ollama" ? systemConfig.ollama_base_url : undefined),
        },
        { headers: getAuthHeaders() }
      );
      if (res.data.status === "success") {
        showToast("success", res.data.message);
      } else {
        showToast("info", res.data.message);
      }
    } catch (err: any) {
      showToast("error", err.response?.data?.detail || "Connection test failed");
    } finally {
      setTestingKey(false);
    }
  };

  const handleSaveKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKeyInput.trim() && selectedProvider.id !== "ollama") {
      showToast("error", "API Key is required");
      return;
    }
    setSavingKey(true);
    try {
      const activeModel = isCustomModel ? customModelInput.trim() : selectedModel;
      await axios.post(
        `${API_BASE}/settings/keys`,
        {
          name: keyName,
          provider: selectedProvider.id,
          api_key: apiKeyInput.trim() || "ollama-local",
          model: activeModel,
          reasoning_effort: reasoningEffort,
          temperature: Number(temperature),
          max_tokens: maxTokens,
          base_url: customBaseUrl || undefined,
          is_active: true,
        },
        { headers: getAuthHeaders() }
      );
      showToast("success", `${selectedProvider.name} API Key saved and set as active provider!`);
      setApiKeyInput("");
      fetchData();
    } catch (err: any) {
      showToast("error", err.response?.data?.detail || "Failed to save API key");
    } finally {
      setSavingKey(false);
    }
  };

  const handleDeleteKey = async (id: string, name: string) => {
    if (!window.confirm(`Are you sure you want to delete "${name}"?`)) return;
    try {
      await axios.delete(`${API_BASE}/settings/keys/${id}`, { headers: getAuthHeaders() });
      showToast("success", "API Key removed");
      setApiKeys((prev) => prev.filter((k) => k.id !== id));
    } catch (err: any) {
      showToast("error", err.response?.data?.detail || "Failed to delete key");
    }
  };

  const handleSaveSystem = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingSystem(true);
    try {
      await axios.post(`${API_BASE}/settings/system`, systemConfig, { headers: getAuthHeaders() });
      showToast("success", "System & alert configurations saved successfully");
    } catch (err: any) {
      showToast("error", err.response?.data?.detail || "Failed to save system settings");
    } finally {
      setSavingSystem(false);
    }
  };

  return (
    <div className="settings-page">
      {/* Toast banner */}
      {toast && (
        <div className={`settings-toast settings-toast--${toast.type}`}>
          <span>{toast.message}</span>
          <button onClick={() => setToast(null)}>×</button>
        </div>
      )}

      {/* Header */}
      <header className="settings-header">
        <div>
          <h1 className="settings-title">System & API Settings</h1>
          <p className="settings-subtitle">
            Configure your AI providers, model preferences, and autonomous agent orchestration parameters.
          </p>
        </div>
        <div className="settings-header-badge">
          <span className="status-dot status-dot--online"></span>
          <span>Engine Ready</span>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="settings-tabs">
        <button
          className={`settings-tab ${activeTab === "api" ? "settings-tab--active" : ""}`}
          onClick={() => setActiveTab("api")}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="2" y="2" width="20" height="8" rx="2"></rect>
            <rect x="2" y="14" width="20" height="8" rx="2"></rect>
            <line x1="6" y1="6" x2="6.01" y2="6"></line>
            <line x1="6" y1="18" x2="6.01" y2="18"></line>
          </svg>
          AI Providers & API Keys
        </button>
        <button
          className={`settings-tab ${activeTab === "system" ? "settings-tab--active" : ""}`}
          onClick={() => setActiveTab("system")}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
          </svg>
          Notifications & Alerts
        </button>
        <button
          className={`settings-tab ${activeTab === "preferences" ? "settings-tab--active" : ""}`}
          onClick={() => setActiveTab("preferences")}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3"></circle>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
          </svg>
          Workspace & Orchestration
        </button>
      </div>

      {/* Tab 1: AI Providers & API Keys */}
      {activeTab === "api" && (
        <div className="settings-content">
          {/* Quick Provider Picker Cards */}
          <div className="providers-grid">
            {PROVIDERS.map((prov) => {
              const isSelected = selectedProvider.id === prov.id;
              const hasKey = apiKeys.some((k) => k.provider === prov.id && k.is_active);

              return (
                <div
                  key={prov.id}
                  className={`provider-card ${isSelected ? "provider-card--selected" : ""}`}
                  onClick={() => handleSelectProvider(prov)}
                >
                  <div className="provider-card__header">
                    <div className="provider-card__icon">{prov.icon}</div>
                    <span className="provider-badge" style={{ borderColor: prov.badgeColor, color: prov.badgeColor }}>
                      {prov.badge}
                    </span>
                  </div>
                  <h3 className="provider-card__name">{prov.name}</h3>
                  <p className="provider-card__desc">{prov.tagline}</p>
                  <div className="provider-card__footer">
                    {hasKey ? (
                      <span className="provider-status provider-status--configured">
                        <span className="status-dot status-dot--online"></span> Configured
                      </span>
                    ) : (
                      <span className="provider-status provider-status--not-set">
                        Not Configured
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Direct Agents Customization Banner */}
          <div className="agents-shortcut-banner">
            <div className="agents-shortcut-banner__text">
              <span className="badge-sparkle">Agent Architecture</span>
              <h4>Customize Agent Roles, System Prompts & Reasoning Depth</h4>
              <p>Tailor specialized prompts for Architects, Coders, Planners, and QA, or create custom specialist roles.</p>
            </div>
            <button
              type="button"
              className="btn btn--agent-nav"
              onClick={() => navigate("/agents")}
            >
              Agents Management & Prompts →
            </button>
          </div>

          {/* Key Configuration Form */}
          <div className="settings-card form-card">
            <div className="form-card__header">
              <div>
                <h2 className="form-card__title">Configure {selectedProvider.name}</h2>
                <p className="form-card__subtitle">
                  Select model parameters, reasoning intensity, and credentials. Keys are stored encrypted.
                </p>
              </div>
              <span className="provider-badge" style={{ borderColor: selectedProvider.badgeColor, color: selectedProvider.badgeColor }}>
                {selectedProvider.badge}
              </span>
            </div>

            <form onSubmit={handleSaveKey} className="settings-form">
              <div className="form-row">
                <div className="form-group flex-1">
                  <label className="form-label">Key Name / Alias</label>
                  <input
                    type="text"
                    className="form-input"
                    value={keyName}
                    onChange={(e) => setKeyName(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group flex-1">
                  <div className="label-with-action">
                    <label className="form-label">Model Selection</label>
                    <button
                      type="button"
                      className="btn-text-action"
                      onClick={handleFetchModels}
                      disabled={fetchingModels}
                    >
                      {fetchingModels ? "Fetching..." : "↻ Fetch Live Models"}
                    </button>
                  </div>

                  {!isCustomModel ? (
                    <select
                      className="form-select"
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                    >
                      {dynamicModels.length > 0 ? (
                        dynamicModels.map((m) => (
                          <option key={m.id} value={m.id}>
                            {m.name} {m.supports_reasoning ? "🧠 [Reasoning]" : ""}
                          </option>
                        ))
                      ) : selectedProvider.models.length > 0 ? (
                        selectedProvider.models.map((m) => (
                          <option key={m} value={m}>
                            {m}
                          </option>
                        ))
                      ) : (
                        <option value="">
                          {language === "fa" ? "مدلی لود نشده — دکمه «دریافت آنلاین مدل‌ها» را بزنید" : "-- Click 'Fetch Live Models' to load models --"}
                        </option>
                      )}
                    </select>
                  ) : (
                    <input
                      type="text"
                      className="form-input"
                      placeholder="e.g. claude-3-7-sonnet or deepseek/deepseek-r1"
                      value={customModelInput}
                      onChange={(e) => setCustomModelInput(e.target.value)}
                      required
                    />
                  )}

                  <label className="checkbox-subtext">
                    <input
                      type="checkbox"
                      checked={isCustomModel}
                      onChange={(e) => setIsCustomModel(e.target.checked)}
                    />
                    <span>Custom model ID / endpoint</span>
                  </label>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group flex-1">
                  <label className="form-label">
                    API Key Secret
                    {selectedProvider.id === "ollama" && (
                      <span className="label-hint"> (Local Ollama does not require an API key)</span>
                    )}
                  </label>
                  <div className="input-with-button">
                    <input
                      type={showKey ? "text" : "password"}
                      className="form-input"
                      placeholder={selectedProvider.keyPlaceholder}
                      value={apiKeyInput}
                      onChange={(e) => setApiKeyInput(e.target.value)}
                      disabled={selectedProvider.id === "ollama"}
                    />
                    {selectedProvider.id !== "ollama" && (
                      <button
                        type="button"
                        className="btn btn-outline btn-toggle-show"
                        onClick={() => setShowKey(!showKey)}
                      >
                        {showKey ? "Hide" : "Show"}
                      </button>
                    )}
                  </div>
                </div>

                <div className="form-group flex-1">
                  <label className="form-label">
                    Custom Base URL / Gateway <span className="label-hint">(Optional)</span>
                  </label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder={selectedProvider.id === "ollama" ? "http://localhost:11434" : "https://api.openai.com/v1 (or proxy)"}
                    value={customBaseUrl}
                    onChange={(e) => setCustomBaseUrl(e.target.value)}
                  />
                </div>
              </div>

              {/* Reasoning & Sampling Row */}
              <div className="form-row form-row--reasoning">
                <div className="form-group flex-1">
                  <label className="form-label">Reasoning Effort (Thinking Tokens)</label>
                  <select
                    className="form-select"
                    value={reasoningEffort}
                    onChange={(e) => setReasoningEffort(e.target.value)}
                  >
                    <option value="none">None (Standard Token Output)</option>
                    <option value="low">Low (Lightweight Verification)</option>
                    <option value="medium">Medium (Balanced Reasoning)</option>
                    <option value="high">High (Deep Architecture & Proofs)</option>
                  </select>
                  <span className="field-hint">Optimized for o1, o3-mini, Claude 3.7 Thinking, & DeepSeek-R1.</span>
                </div>

                <div className="form-group flex-1">
                  <label className="form-label">Temperature: {temperature}</label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    className="form-range"
                    value={temperature}
                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  />
                  <span className="field-hint">0.0 = Deterministic Code; 1.0 = Creative Exploration.</span>
                </div>

                <div className="form-group flex-1">
                  <label className="form-label">Max Tokens</label>
                  <input
                    type="number"
                    className="form-input"
                    value={maxTokens}
                    onChange={(e) => setMaxTokens(Number(e.target.value))}
                    min={100}
                    max={64000}
                  />
                </div>
              </div>

              <div className="form-actions-bar">
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={handleGetRecommendations}
                  disabled={fetchingRecommendations}
                >
                  {fetchingRecommendations 
                    ? (language === "fa" ? "در حال تحلیل و استخراج..." : "Analyzing Models...") 
                    : (language === "fa" ? "💡 پیشنهاد هوشمند مدل‌ها برای ایجنت‌ها" : "💡 Smart Role Recommendations")}
                </button>
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={handleTestKey}
                  disabled={testingKey}
                >
                  {testingKey 
                    ? (language === "fa" ? "در حال تست..." : "Testing...") 
                    : (language === "fa" ? "تست اتصال" : "Test Connection")}
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={savingKey}
                >
                  {savingKey 
                    ? (language === "fa" ? "در حال ذخیره..." : "Saving...") 
                    : (language === "fa" ? "ذخیره و فعال‌سازی" : "Save & Set Active")}
                </button>
              </div>
            </form>
          </div>

          {/* Smart AI Role Recommendations */}
          {recommendations.length > 0 && (
            <div className="recommendations-card">
              <div className="recommendations-header">
                <div>
                  <div className="recommendations-header__title">
                    <span>🤖</span>
                    <h3>
                      {language === "fa"
                        ? `پیشنهادات هوشمند تخصیص مدل به ایجنت‌ها (${selectedProvider.name})`
                        : `Smart Model Recommendations per Agent Role (${selectedProvider.name})`}
                    </h3>
                  </div>
                  <p className="form-card__subtitle" style={{ margin: "4px 0 0 0" }}>
                    {language === "fa"
                      ? "سیستم به طور خودکار بهترین مدل و میزان استدلال (Reasoning) را متناسب با وظایف تخصصی هر نقش استخراج کرده است."
                      : "The system automatically mapped the best models and reasoning tokens to each specialist agent role."}
                  </p>
                </div>
                <div className="recommendations-header__actions">
                  <button
                    type="button"
                    className="btn--apply-all"
                    onClick={handleApplyRecommendations}
                    disabled={applyingRecommendations}
                  >
                    <span>⚡</span>
                    <span>
                      {applyingRecommendations
                        ? (language === "fa" ? "در حال اعمال..." : "Applying...")
                        : (language === "fa" ? "اعمال به تمام ایجنت‌ها" : "Apply to All Agents")}
                    </span>
                  </button>
                </div>
              </div>

              <div className="recommendations-table-wrap">
                <table className="recs-table">
                  <thead>
                    <tr>
                      <th>{language === "fa" ? "نقش ایجنت" : "Agent Role"}</th>
                      <th>{language === "fa" ? "مدل پیشنهادی" : "Recommended Model"}</th>
                      <th>{language === "fa" ? "سطح استدلال" : "Reasoning"}</th>
                      <th>{language === "fa" ? "دلیل بهینه‌سازی و تطبیق" : "Optimization Rationale"}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recommendations.map((rec, idx) => (
                      <tr key={idx}>
                        <td>
                          <div className="rec-agent-cell">
                            <div className="rec-avatar">
                              {rec.role === "chief_orchestrator" ? "👑" : "⚡"}
                            </div>
                            <div>
                              <div className="rec-name">
                                {language === "fa" && rec.codename_fa ? rec.codename_fa : rec.codename} ({rec.agent_name})
                              </div>
                              <div className="rec-role">role: {rec.role}</div>
                            </div>
                          </div>
                        </td>
                        <td>
                          {dynamicModels.length > 0 ? (
                            <select
                              className="form-select rec-model-select"
                              style={{ padding: "4px 8px", fontSize: "0.82rem", minWidth: "190px", maxWidth: "260px" }}
                              value={rec.recommended_model}
                              onChange={(e) => {
                                const newModel = e.target.value;
                                setRecommendations((prev) =>
                                  prev.map((r, i) => (i === idx ? { ...r, recommended_model: newModel } : r))
                                );
                              }}
                            >
                              {!dynamicModels.some((m) => m.id === rec.recommended_model) && (
                                <option value={rec.recommended_model}>{rec.recommended_model}</option>
                              )}
                              {dynamicModels.map((m) => (
                                <option key={m.id} value={m.id}>
                                  {m.id}
                                </option>
                              ))}
                            </select>
                          ) : (
                            <span className="rec-model-badge">{rec.recommended_model}</span>
                          )}
                        </td>
                        <td>
                          <span className={`rec-effort-badge rec-effort-badge--${rec.recommended_effort || "none"}`}>
                            {rec.recommended_effort?.toUpperCase() || "NONE"}
                          </span>
                        </td>
                        <td>
                          <span className="rec-reason">{rec.reason}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Active Configured Keys List */}
          <div className="settings-card">
            <h2 className="form-card__title">Configured API Keys</h2>
            <p className="form-card__subtitle">
              All stored provider keys. The primary active key is utilized by autonomous worker agents.
            </p>

            {loading ? (
              <p className="settings-loading">Loading credentials...</p>
            ) : apiKeys.length === 0 ? (
              <div className="keys-empty-state">
                <p>No API keys configured yet. Select a provider above and save your credentials to enable autonomous tasks.</p>
              </div>
            ) : (
              <div className="keys-table-container">
                <table className="keys-table">
                  <thead>
                    <tr>
                      <th>Provider</th>
                      <th>Alias</th>
                      <th>Model</th>
                      <th>Masked Key</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {apiKeys.map((key) => (
                      <tr key={key.id}>
                        <td>
                          <span className="provider-tag">{key.provider.toUpperCase()}</span>
                        </td>
                        <td className="key-name">{key.name}</td>
                        <td>{key.model || "Default"}</td>
                        <td>
                          <code className="key-masked">{key.masked_key}</code>
                        </td>
                        <td>
                          <span className="status-badge online">
                            <span className="status-dot"></span> Active
                          </span>
                        </td>
                        <td>
                          <button
                            className="btn-delete"
                            onClick={() => handleDeleteKey(key.id, key.name)}
                            title="Delete Key"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: System & Notifications */}
      {activeTab === "system" && (
        <div className="settings-content">
          <div className="settings-card">
            <h2 className="form-card__title">Telegram Notification Alerts</h2>
            <p className="form-card__subtitle">
              Receive real-time notifications for task milestones, approval requests, and agent errors via Telegram bot.
            </p>

            <form onSubmit={handleSaveSystem} className="settings-form">
              <div className="toggle-row">
                <div>
                  <div className="toggle-title">Enable Telegram Alerts</div>
                  <div className="toggle-desc">Forward critical execution events to your Telegram chat.</div>
                </div>
                <label className="switch">
                  <input
                    type="checkbox"
                    checked={systemConfig.telegram_notifications}
                    onChange={(e) =>
                      setSystemConfig({ ...systemConfig, telegram_notifications: e.target.checked })
                    }
                  />
                  <span className="slider round"></span>
                </label>
              </div>

              {systemConfig.telegram_notifications && (
                <div className="form-row" style={{ marginTop: "1rem" }}>
                  <div className="form-group">
                    <label className="form-label">Telegram Bot Token</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
                      value={systemConfig.telegram_bot_token || ""}
                      onChange={(e) =>
                        setSystemConfig({ ...systemConfig, telegram_bot_token: e.target.value })
                      }
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Telegram Chat ID</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="-100123456789"
                      value={systemConfig.telegram_chat_id || ""}
                      onChange={(e) =>
                        setSystemConfig({ ...systemConfig, telegram_chat_id: e.target.value })
                      }
                    />
                  </div>
                </div>
              )}

              <div className="form-actions-align" style={{ marginTop: "1.5rem" }}>
                <button type="submit" className="btn btn-primary" disabled={savingSystem}>
                  {savingSystem ? "Saving..." : "Save Notification Settings"}
                </button>
              </div>
            </form>
          </div>

          <div className="settings-card">
            <h2 className="form-card__title">Local Inference Engine (Ollama)</h2>
            <p className="form-card__subtitle">
              Configure the host and port for your local Ollama server.
            </p>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Ollama API Host Endpoint</label>
                <input
                  type="text"
                  className="form-input"
                  value={systemConfig.ollama_base_url}
                  onChange={(e) =>
                    setSystemConfig({ ...systemConfig, ollama_base_url: e.target.value })
                  }
                />
              </div>
              <div className="form-group form-actions-align">
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => showToast("info", "Ollama connection configured for localhost:11434")}
                >
                  Verify Ollama Host
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Workspace & Orchestration */}
      {activeTab === "preferences" && (
        <div className="settings-content">
          <div className="settings-card">
            <h2 className="form-card__title">Orchestration & Concurrency</h2>
            <p className="form-card__subtitle">
              Adjust worker resource allocation and agent execution parameters.
            </p>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Max Concurrent Workers: {systemConfig.max_workers}</label>
                <input
                  type="range"
                  min="1"
                  max="8"
                  value={systemConfig.max_workers}
                  onChange={(e) =>
                    setSystemConfig({ ...systemConfig, max_workers: Number(e.target.value) })
                  }
                  style={{ width: "100%", accentColor: "#007BFF" }}
                />
                <p className="label-hint">Defines how many agent tasks can run simultaneously.</p>
              </div>
              <div className="form-group">
                <label className="form-label">Preferred Interface Language</label>
                <select
                  className="form-select"
                  value={systemConfig.preferred_language}
                  onChange={(e) =>
                    setSystemConfig({ ...systemConfig, preferred_language: e.target.value })
                  }
                >
                  <option value="en">English (Default)</option>
                  <option value="fa">Persian (فارسی)</option>
                </select>
              </div>
            </div>

            <div className="form-actions-align" style={{ marginTop: "1.5rem" }}>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => showToast("success", "Orchestration preferences updated")}
              >
                Save Preferences
              </button>
            </div>
          </div>

          <div className="settings-card">
            <h2 className="form-card__title">Theme & Design System</h2>
            <p className="form-card__subtitle">
              NexusForge utilizes the Obsidian & Electric Azure high-contrast theme.
            </p>
            <div className="theme-preview">
              <div className="theme-chip" style={{ background: "#090A0F", border: "1px solid #007BFF" }}>
                <span>Canvas (#090A0F)</span>
              </div>
              <div className="theme-chip" style={{ background: "#12151E", border: "1px solid rgba(255,255,255,0.1)" }}>
                <span>Surfaces (#12151E)</span>
              </div>
              <div className="theme-chip" style={{ background: "#007BFF", color: "#fff" }}>
                <span>Accent (#007BFF)</span>
              </div>
              <div className="theme-chip" style={{ background: "#10B981", color: "#fff" }}>
                <span>Healthy (#10B981)</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Settings;
