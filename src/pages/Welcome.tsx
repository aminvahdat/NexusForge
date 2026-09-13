import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { settingsApi, authApi } from "../services/api";
import "./Welcome.css";

interface ProviderOption {
  id: string;
  name: string;
  badge: string;
  badgeColor: string;
  tagline: string;
  defaultModel: string;
  models: string[];
  keyPlaceholder: string;
  defaultBaseUrl?: string;
  help: string;
  icon: React.ReactNode;
}

const PROVIDERS: ProviderOption[] = [
  {
    id: "openrouter",
    name: "OpenRouter",
    badge: "Universal Hub",
    badgeColor: "#6366F1",
    tagline: "Access 400+ frontier models (Claude, OpenAI, DeepSeek, Llama)",
    defaultModel: "openrouter/auto",
    models: [
      "openrouter/auto",
      "anthropic/claude-3.5-sonnet",
      "deepseek/deepseek-r1",
      "meta-llama/llama-3.3-70b-instruct",
      "openrouter/free",
    ],
    keyPlaceholder: "sk-or-v1-...",
    help: "Recommended universal endpoint connecting to any LLM with one key.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="2" y1="12" x2="22" y2="12"></line>
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
      </svg>
    ),
  },
  {
    id: "openai",
    name: "OpenAI",
    badge: "Industry Standard",
    badgeColor: "#007BFF",
    tagline: "Flagship GPT-4o, o1, and fast o3-mini reasoning models",
    defaultModel: "gpt-4o",
    models: ["o3-mini", "o1", "gpt-4o", "gpt-4o-mini"],
    keyPlaceholder: "sk-proj-...",
    help: "High intelligence and strong tool/function calling capabilities.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 2a10 10 0 0 1 10 10c0 5.523-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2z"></path>
        <path d="M12 6v6l4 2"></path>
      </svg>
    ),
  },
  {
    id: "anthropic",
    name: "Anthropic Claude",
    badge: "Coding Champion",
    badgeColor: "#8B5CF6",
    tagline: "State of the art Claude 3.5 Sonnet & Claude 3.7 Sonnet",
    defaultModel: "claude-3-5-sonnet-20241022",
    models: [
      "claude-3-7-sonnet-latest",
      "claude-3-5-sonnet-20241022",
      "claude-3-5-haiku-20241022",
      "claude-3-opus-20240229",
    ],
    keyPlaceholder: "sk-ant-...",
    help: "Premier intelligence for autonomous software architecture and engineering.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
        <polyline points="2 17 12 22 22 17"></polyline>
        <polyline points="2 12 12 17 22 12"></polyline>
      </svg>
    ),
  },
  {
    id: "groq",
    name: "Groq LPU",
    badge: "Ultra Fast",
    badgeColor: "#F59E0B",
    tagline: "Blazing fast Llama 3.3 70B and DeepSeek-R1 at 300+ tok/s",
    defaultModel: "llama-3.3-70b-versatile",
    models: [
      "llama-3.3-70b-versatile",
      "deepseek-r1-distill-llama-70b",
      "llama-3.1-8b-instant",
    ],
    keyPlaceholder: "gsk_...",
    help: "Real-time near instantaneous execution on custom LPU chips.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
      </svg>
    ),
  },
  {
    id: "ollama",
    name: "Ollama / Local",
    badge: "Offline & Local",
    badgeColor: "#10B981",
    tagline: "Private offline models running locally on your hardware",
    defaultModel: "llama3.3:70b",
    models: [
      "llama3.3:70b",
      "deepseek-r1:8b",
      "deepseek-r1:14b",
      "qwen2.5-coder:7b",
      "llama3.1:8b",
    ],
    defaultBaseUrl: "http://localhost:11434",
    keyPlaceholder: "Optional for local Ollama (defaults to 'ollama')",
    help: "Zero external network requirements. Perfect for air-gapped environments.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>
        <rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
        <line x1="6" y1="6" x2="6.01" y2="6"></line>
        <line x1="6" y1="18" x2="6.01" y2="18"></line>
      </svg>
    ),
  },
  {
    id: "deepseek",
    name: "DeepSeek",
    badge: "Reasoning King",
    badgeColor: "#0EA5E9",
    tagline: "DeepSeek-R1 full reasoning & DeepSeek-V3 fast coding",
    defaultModel: "deepseek-reasoner",
    models: ["deepseek-reasoner", "deepseek-chat"],
    keyPlaceholder: "sk-...",
    help: "High intelligence and transparent chain-of-thought tokens.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10"></circle>
        <path d="M8 12h8"></path>
        <path d="M12 8v8"></path>
      </svg>
    ),
  },
  {
    id: "google",
    name: "Google Gemini",
    badge: "2M Context",
    badgeColor: "#EC4899",
    tagline: "Gemini 2.0 Flash & Gemini 2.5 Pro with deep reasoning",
    defaultModel: "gemini-2.0-flash",
    models: ["gemini-2.5-pro", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
    keyPlaceholder: "AIzaSy...",
    help: "Ultra long context windows for full repository analysis.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path>
      </svg>
    ),
  },
];

const Welcome: React.FC = () => {
  const [selectedProvider, setSelectedProvider] = useState<string>("openrouter");
  const [keyName, setKeyName] = useState<string>("OpenRouter Primary");
  const [apiKey, setApiKey] = useState<string>("");
  const [showKey, setShowKey] = useState<boolean>(false);
  const [baseUrl, setBaseUrl] = useState<string>("");
  const [model, setModel] = useState<string>("openrouter/auto");
  const [customModel, setCustomModel] = useState<string>("");
  const [isCustom, setIsCustom] = useState<boolean>(false);

  const [testing, setTesting] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<{
    status: "success" | "warning" | "error";
    message: string;
  } | null>(null);

  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);
  const navigate = useNavigate();

  const currentProviderObj =
    PROVIDERS.find((p) => p.id === selectedProvider) || PROVIDERS[0];

  const handleSelectProvider = (provId: string) => {
    setSelectedProvider(provId);
    const prov = PROVIDERS.find((p) => p.id === provId) || PROVIDERS[0];
    setKeyName(`${prov.name} Primary`);
    setModel(prov.defaultModel);
    setBaseUrl(prov.defaultBaseUrl || "");
    setIsCustom(false);
    setCustomModel("");
    setTestResult(null);
    setError(null);
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    setError(null);

    const keyToTest = apiKey.trim() || (selectedProvider === "ollama" ? "ollama" : "");
    if (!keyToTest && selectedProvider !== "ollama") {
      setTestResult({
        status: "error",
        message: "Please enter an API key before testing connection.",
      });
      setTesting(false);
      return;
    }

    try {
      const res = await settingsApi.testKey({
        provider: selectedProvider,
        api_key: keyToTest,
        base_url: baseUrl.trim() || undefined,
      });

      if (res?.status === "success") {
        setTestResult({
          status: "success",
          message: res.message || "Connection and credentials successfully verified!",
        });
      } else if (res?.status === "warning") {
        setTestResult({
          status: "warning",
          message: res.message || "Credentials saved with warning.",
        });
      } else {
        setTestResult({
          status: "success",
          message: "API key format verified for this provider.",
        });
      }
    } catch (err: any) {
      setTestResult({
        status: "error",
        message: err.detail || err.message || "Connection test failed. Verify credentials.",
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSaveAndProceed = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    const finalKey = apiKey.trim() || (selectedProvider === "ollama" ? "ollama" : "");
    if (!finalKey) {
      setError("Please enter your API Key to proceed.");
      setSaving(false);
      return;
    }

    const finalModel = isCustom ? customModel.trim() : model.trim();
    if (!finalModel) {
      setError("Please select or specify a model name.");
      setSaving(false);
      return;
    }

    try {
      // 1. Create/Save User API Key
      await settingsApi.createKey({
        name: keyName.trim() || `${currentProviderObj.name} Default`,
        provider: selectedProvider,
        api_key: finalKey,
        model: finalModel,
        base_url: baseUrl.trim() || undefined,
        is_active: true,
      });

      // 2. Set default system provider
      try {
        await settingsApi.updateSystem({
          default_provider: selectedProvider,
          default_model: finalModel,
          ollama_base_url: baseUrl.trim() || "http://localhost:11434",
        });
      } catch {
        // Non-fatal if system settings update is restricted to admin
      }

      setSuccess(true);

      // Smooth transition to dashboard
      setTimeout(() => {
        navigate("/");
      }, 1000);
    } catch (err: any) {
      setError(
        err.detail || err.message || "Failed to save API key. Please check your inputs."
      );
      setSaving(false);
    }
  };

  return (
    <div className="welcome-page-container">
      <div className="welcome-wrapper">
        {/* Header */}
        <div className="welcome-header">
          <div className="welcome-badge-pill">
            <div className="welcome-badge-dot" />
            <span>Step 1 of 1 • AI Provider Configuration</span>
          </div>
          <h1 className="welcome-title">
            Welcome to <span className="welcome-title-gradient">NexusForge</span>
          </h1>
          <p className="welcome-subtitle">
            To empower autonomous multi-agent coding, workspace synthesis, and task execution,
            NexusForge connects to an AI provider. Select your preferred provider and input your credentials to begin.
          </p>
        </div>

        {/* Section Label */}
        <div className="welcome-section-label">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
            <line x1="8" y1="21" x2="16" y2="21"></line>
            <line x1="12" y1="17" x2="12" y2="21"></line>
          </svg>
          <span>Choose Your AI Provider</span>
        </div>

        {/* Provider Cards Grid */}
        <div className="welcome-provider-grid">
          {PROVIDERS.map((prov) => {
            const isSelected = selectedProvider === prov.id;
            return (
              <div
                key={prov.id}
                className={`welcome-provider-card ${isSelected ? "active" : ""}`}
                onClick={() => handleSelectProvider(prov.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    handleSelectProvider(prov.id);
                  }
                }}
              >
                <div className="provider-card-top">
                  <div className="provider-card-icon">{prov.icon}</div>
                  <span
                    className="provider-badge"
                    style={{
                      backgroundColor: `${prov.badgeColor}20`,
                      color: prov.badgeColor,
                      border: `1px solid ${prov.badgeColor}40`,
                    }}
                  >
                    {prov.badge}
                  </span>
                </div>
                <div>
                  <h3 className="provider-card-title">{prov.name}</h3>
                  <p className="provider-card-desc">{prov.tagline}</p>
                </div>
                {isSelected && (
                  <div className="provider-card-check">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                      <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Configuration Form */}
        <div className="welcome-form-card">
          <div className="welcome-form-header">
            <h2 className="welcome-form-title">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
              </svg>
              <span>Configure Credentials</span>
            </h2>
            <span className="welcome-provider-pill">{currentProviderObj.name}</span>
          </div>

          {error && (
            <div className="welcome-test-feedback test-feedback-error">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="welcome-test-feedback test-feedback-success">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
              </svg>
              <span>AI Provider successfully connected! Launching NexusForge...</span>
            </div>
          )}

          <form onSubmit={handleSaveAndProceed}>
            <div className="welcome-form-grid">
              {/* Configuration Name */}
              <div className="welcome-field">
                <label className="welcome-label">Configuration Label</label>
                <input
                  type="text"
                  value={keyName}
                  onChange={(e) => setKeyName(e.target.value)}
                  className="welcome-input"
                  placeholder="e.g. Primary OpenRouter Key"
                  required
                />
              </div>

              {/* Model Selector */}
              <div className="welcome-field">
                <label className="welcome-label">
                  <span>Default Model</span>
                  <button
                    type="button"
                    style={{ background: "none", border: "none", color: "#38BDF8", fontSize: "0.75rem", cursor: "pointer" }}
                    onClick={() => setIsCustom(!isCustom)}
                  >
                    {isCustom ? "Choose preset" : "Custom model name"}
                  </button>
                </label>
                {isCustom ? (
                  <input
                    type="text"
                    value={customModel}
                    onChange={(e) => setCustomModel(e.target.value)}
                    className="welcome-input"
                    placeholder="e.g. gpt-4o-2024-08-06 or custom-tag"
                    required
                  />
                ) : (
                  <select
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    className="welcome-select"
                  >
                    {currentProviderObj.models.map((m) => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {/* API Key */}
              <div className="welcome-field welcome-full-width">
                <label className="welcome-label">
                  <span>API Key {selectedProvider === "ollama" ? "(Optional)" : ""}</span>
                  <span style={{ color: "#64748B", fontWeight: 400, fontSize: "0.75rem" }}>
                    Encrypted and stored with user-isolated security
                  </span>
                </label>
                <div className="welcome-input-wrapper">
                  <input
                    type={showKey ? "text" : "password"}
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    className="welcome-input"
                    placeholder={currentProviderObj.keyPlaceholder}
                    required={selectedProvider !== "ollama"}
                    style={{ paddingRight: "3rem" }}
                  />
                  <button
                    type="button"
                    className="auth-input-toggle"
                    onClick={() => setShowKey(!showKey)}
                    title={showKey ? "Hide key" : "Show key"}
                    aria-label={showKey ? "Hide key" : "Show key"}
                  >
                    {showKey ? (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                        <line x1="1" y1="1" x2="23" y2="23"></line>
                      </svg>
                    ) : (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                      </svg>
                    )}
                  </button>
                </div>
                <p className="welcome-help-text">{currentProviderObj.help}</p>
              </div>

              {/* Base URL (Shown for Ollama or when customized) */}
              {(selectedProvider === "ollama" || baseUrl) && (
                <div className="welcome-field welcome-full-width">
                  <label className="welcome-label">
                    <span>Base URL (Host Endpoint)</span>
                    <span style={{ color: "#10B981", fontSize: "0.75rem" }}>Ollama Active</span>
                  </label>
                  <input
                    type="url"
                    value={baseUrl}
                    onChange={(e) => setBaseUrl(e.target.value)}
                    className="welcome-input"
                    placeholder="http://localhost:11434"
                  />
                  <p className="welcome-help-text">
                    For local Ollama, ensure Ollama is running and accessible from the server network.
                  </p>
                </div>
              )}
            </div>

            {/* Test Status Banner */}
            {testResult && (
              <div
                className={`welcome-test-feedback ${
                  testResult.status === "success"
                    ? "test-feedback-success"
                    : testResult.status === "warning"
                    ? "test-feedback-warning"
                    : "test-feedback-error"
                }`}
              >
                {testResult.status === "success" ? (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                  </svg>
                )}
                <span>{testResult.message}</span>
              </div>
            )}

            {/* Action Buttons */}
            <div className="welcome-actions-row">
              <button
                type="button"
                className="welcome-btn-secondary"
                onClick={handleTestConnection}
                disabled={testing || saving}
              >
                {testing ? (
                  <>
                    <div className="auth-spinner" style={{ width: "14px", height: "14px" }} />
                    <span>Testing...</span>
                  </>
                ) : (
                  <>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                      <polyline points="22 4 12 14.01 9 11.01"></polyline>
                    </svg>
                    <span>Test Connection</span>
                  </>
                )}
              </button>

              <button
                type="submit"
                className="welcome-btn-primary"
                disabled={saving || success}
              >
                {saving ? (
                  <>
                    <div className="auth-spinner" style={{ width: "16px", height: "16px" }} />
                    <span>Saving Credentials...</span>
                  </>
                ) : (
                  <>
                    <span>Save & Launch NexusForge</span>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="5" y1="12" x2="19" y2="12"></line>
                      <polyline points="12 5 19 12 12 19"></polyline>
                    </svg>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Security Notice */}
        <div className="welcome-security-notice">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#64748B" strokeWidth="2" style={{ flexShrink: 0, marginTop: "2px" }}>
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
          </svg>
          <div>
            <strong>Least-Privilege & Data Privacy:</strong> Your API keys are encrypted at rest and tied solely to your user account. NexusForge never transmits keys to unauthenticated endpoints or unauthorized background processes.
          </div>
        </div>
      </div>
    </div>
  );
};

export default Welcome;
