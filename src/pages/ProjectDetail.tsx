import React, { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { projectApi, taskApi } from "../services/api";
import { useLanguage } from "../context/LanguageContext";
import { Project, ProjectMessage, WorkspaceFile, Task } from "../types";
import "./ProjectDetail.css";


const ProjectDetail: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { language } = useLanguage();
  const isFa = language === "fa";

  // State
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Chat State (Hermes / Arya)
  const [messages, setMessages] = useState<ProjectMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Workspace & Files State
  const [activeTab, setActiveTab] = useState<"files" | "terminal" | "traces" | "models">("files");
  const [files, setFiles] = useState<WorkspaceFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>("");
  const [fileLoading, setFileLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  // Reasoning Traces State
  const [traces, setTraces] = useState<any[]>([]);

  // Terminal State
  const [termCommand, setTermCommand] = useState("dir");
  const [termOutput, setTermOutput] = useState<string>("$ NexusForge Terminal Ready\n$ Enter command or select quick action.\n");
  const [termRunning, setTermRunning] = useState(false);

  // Tasks State
  const [tasks, setTasks] = useState<Task[]>([]);

  // Execution / Build State
  const [isRunning, setIsRunning] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [editWsPath, setEditWsPath] = useState("");
  const [activePipelineStep, setActivePipelineStep] = useState<number>(-1);

  // Collapsed states for thinking blocks
  const [openThinkingMap, setOpenThinkingMap] = useState<{ [msgId: string]: boolean }>({});

  const toggleThinking = (msgId: string) => {
    setOpenThinkingMap((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  // 1. Initial Load
  const fetchProjectData = async () => {
    if (!projectId) return;
    try {
      const p = await projectApi.getById(projectId);
      setProject(p);
      setEditWsPath(p.workspace_path || "");

      // Load Messages
      const msgRes = await projectApi.getMessages(projectId);
      const safeMsgs = (msgRes?.messages || []).filter(
        (m): m is ProjectMessage => Boolean(m && m.id && m.sender)
      );
      setMessages(safeMsgs);

      // Load Tasks
      try {
        const tList = await taskApi.getAllByProject(projectId);
        setTasks(tList || []);
      } catch {
        setTasks([]);
      }

      // Load Files & Traces
      await refreshFiles();
    } catch (err: any) {
      setError(err?.detail || (isFa ? "خطا در دریافت اطلاعات پروژه" : "Error loading project"));
    } finally {
      setLoading(false);
    }
  };

  const refreshFiles = async () => {
    if (!projectId) return;
    try {
      const res = await projectApi.getFiles(projectId);
      const list = res.files || [];
      setFiles(list);

      // Check if agent_reasoning_trace.json exists to load traces
      const traceFile = list.find((f: any) => f.name === "agent_reasoning_trace.json");
      if (traceFile) {
        try {
          const tRes = await projectApi.getFileContent(projectId, traceFile.path);
          const parsed = JSON.parse(tRes.content);
          if (Array.isArray(parsed)) setTraces(parsed);
        } catch (e) {
          console.warn("Could not parse traces", e);
        }
      }

      if (list.length > 0 && !selectedFile) {
        const preferred = list.find((f: any) => f.name === "main.py") || list.find((f: any) => f.name === "index.html") || list[0];
        handleSelectFile(preferred.path);
      }
    } catch (e) {
      console.warn("Files fetch error:", e);
    }
  };

  useEffect(() => {
    fetchProjectData();
  }, [projectId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  // Select File to View
  const handleSelectFile = async (path: string) => {
    if (!projectId) return;
    setSelectedFile(path);
    setFileLoading(true);
    try {
      const res = await projectApi.getFileContent(projectId, path);
      setFileContent(res.content);
    } catch (e) {
      setFileContent(isFa ? "// خطا در خواندن محتوای فایل" : "// Error loading file content");
    } finally {
      setFileLoading(false);
    }
  };

  // Copy Code
  const handleCopyCode = () => {
    if (!fileContent) return;
    navigator.clipboard.writeText(fileContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Send Message to Hermes / Arya
  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || chatInput).trim();
    if (!text || !projectId || isSending) return;

    setChatInput("");
    setIsSending(true);

    const tempUserMsg: ProjectMessage = {
      id: "temp-" + Date.now(),
      project_id: projectId,
      sender: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const res = await projectApi.sendMessage(projectId, text);
      const incoming: ProjectMessage[] = [];
      if (res.user_message && res.user_message.id && res.user_message.sender) {
        incoming.push(res.user_message);
      }
      const replyMsg = res.hermes_message || (res as any).assistant_message;
      if (replyMsg && replyMsg.id && replyMsg.sender) {
        incoming.push(replyMsg);
      }

      setMessages((prev) => [
        ...prev.filter((m) => m && m.id && m.id !== tempUserMsg.id),
        ...incoming,
      ]);

      if (res.trigger_build) {
        await refreshFiles();
      }
    } catch (err: any) {
      alert(isFa ? "خطا در ارسال پیام: " + (err.detail || err.message) : "Failed to send message: " + (err.detail || err.message));
    } finally {
      setIsSending(false);
    }
  };

  // Trigger 12-Agent Project Build & Run
  const handleTriggerBuild = async () => {
    if (!projectId || isRunning) return;
    setIsRunning(true);
    setActivePipelineStep(0);

    // Animate the 12-agent pipeline indicator
    const stepInterval = setInterval(() => {
      setActivePipelineStep((prev) => {
        if (prev >= SQUAD_12_AGENTS.length - 1) {
          clearInterval(stepInterval);
          return SQUAD_12_AGENTS.length - 1;
        }
        return prev + 1;
      });
    }, 1700);

    try {
      await projectApi.run(projectId);
      await refreshFiles();
      await fetchProjectData();
      setActiveTab("files");
    } catch (e: any) {
      alert(isFa ? "خطا در اجرای پایپ‌لاین ایجنت‌ها: " + (e.detail || e.message) : "Build failed: " + (e.detail || e.message));
    } finally {
      clearInterval(stepInterval);
      setIsRunning(false);
      setActivePipelineStep(-1);
    }
  };

  // Run Terminal Command
  const handleRunTerminal = async (cmdToRun?: string) => {
    const cmd = cmdToRun || termCommand;
    if (!cmd.trim() || !projectId || termRunning) return;

    setTermRunning(true);
    setTermOutput((prev) => prev + `\n$ ${cmd}\n`);

    try {
      const res = await projectApi.runTerminal(projectId, cmd);
      const out = res.stdout || res.stderr || (res.exit_code === 0 ? "✓ Command executed with exit code 0" : "Process exited");
      setTermOutput((prev) => prev + out + "\n");
    } catch (e: any) {
      setTermOutput((prev) => prev + `Error: ${e.detail || e.message}\n`);
    } finally {
      setTermRunning(false);
    }
  };

  // Save Workspace Settings
  const handleSaveSettings = async () => {
    if (!projectId) return;
    try {
      const updated = await projectApi.update(projectId, {
        workspace_path: editWsPath.trim() || undefined,
      });
      setProject(updated);
      setShowSettingsModal(false);
      await refreshFiles();
    } catch (e: any) {
      alert(isFa ? "خطا در ذخیره تنظیمات: " + (e.detail || e.message) : "Failed to save settings: " + (e.detail || e.message));
    }
  };

  // Delete Project
  const handleDelete = async () => {
    if (!projectId || !window.confirm(isFa ? "آیا از حذف این پروژه اطمینان دارید؟" : "Delete project?")) return;
    try {
      await projectApi.delete(projectId);
      navigate("/projects");
    } catch (e: any) {
      alert(isFa ? "خطا در حذف پروژه: " + (e.detail || e.message) : "Failed to delete project: " + (e.detail || e.message));
    }
  };

  if (loading) {
    return (
      <div className="project-detail-container loading-state">
        <div className="spinner"></div>
        <p>{isFa ? "در حال فراخوانی استودیوی نکسوس‌فورج..." : "Loading NexusForge Studio..."}</p>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="project-detail-container error-state">
        <h3>{isFa ? "پروژه یافت نشد" : "Project Not Found"}</h3>
        <p>{error}</p>
        <button className="btn-primary" onClick={() => navigate("/projects")}>
          {isFa ? "بازگشت به فهرست پروژه‌ها" : "Back to Projects"}
        </button>
      </div>
    );
  }

  // Parse message content for Hermes terminal <thinking> and [TOOL_CALL] blocks
  const renderMessageContent = (msg: ProjectMessage) => {
    if (!msg || typeof msg.content !== "string") return null;
    const raw = msg.content;
    const thinkingMatch = raw.match(/<thinking>([\s\S]*?)<\/thinking>/);
    const hasThinking = !!thinkingMatch;
    const thinkingText = thinkingMatch ? thinkingMatch[1].trim() : "";
    const cleanContent = raw.replace(/<thinking>[\s\S]*?<\/thinking>/, "").trim();

    return (
      <div className="message-content-wrapper">
        {hasThinking && (
          <div className="terminal-thinking-box">
            <div className="thinking-header" onClick={() => toggleThinking(msg.id)}>
              <span className="thinking-title">
                <span className="terminal-cursor">&gt;_</span>
                <span>{isFa ? "تفکر عمیق مدل (Chain of Thought)" : "Deep Model Reasoning"}</span>
              </span>
              <button className="thinking-toggle-btn">
                {openThinkingMap[msg.id] ? (isFa ? "بستن ▲" : "Hide ▲") : (isFa ? "مشاهده تحلیل ▼" : "View Reasoning ▼")}
              </button>
            </div>
            {openThinkingMap[msg.id] && (
              <pre className="thinking-content">
                <code>{thinkingText}</code>
              </pre>
            )}
          </div>
        )}

        <div className="message-body">
          {cleanContent.split("\n").map((line, idx) => {
            if (line.includes("[TOOL_CALL:") || line.includes("[TOOL_RESULT:")) {
              return (
                <div key={idx} className="tool-call-line">
                  <span className="tool-call-tag">{line.includes("[TOOL_CALL:") ? "⚙️ TOOL" : "✓ RESULT"}</span>
                  <code>{line}</code>
                </div>
              );
            }
            return <p key={idx}>{line}</p>;
          })}
        </div>
      </div>
    );
  };

  return (
    <div className={`project-studio ${isFa ? "rtl" : "ltr"}`}>
      {/* 1. TOP MINIMALIST HEADER */}
      <header className="studio-header">
        <div className="header-left">
          <button className="btn-back" onClick={() => navigate("/projects")}>
            {isFa ? "← پروژه‌ها" : "← Projects"}
          </button>
          <div className="project-identity">
            <h1 className="project-title">{project.name}</h1>
            <span className="workspace-badge" onClick={() => setShowSettingsModal(true)} title={isFa ? "کلیک برای ویرایش مسیر پوشه کاری" : "Click to edit workspace"}>
              📁 {project.workspace_path || `workspaces/${project.id.slice(0, 8)}`}
            </span>
          </div>
        </div>

        <div className="header-right">
          <span className={`status-pill ${isRunning ? "running" : "ready"}`}>
            {isRunning ? (isFa ? "⚡ هدایت بی‌وقفه ۱۲ ایجنت..." : "⚡ 12 Agents Mobilized...") : (isFa ? "🟢 تیم ۱۲ ایجنتی آماده" : "🟢 12 Agents Ready")}
          </span>

          <button
            className={`btn-build ${isRunning ? "loading" : ""}`}
            onClick={handleTriggerBuild}
            disabled={isRunning}
          >
            {isRunning ? (
              <>
                <span className="spinner-mini"></span>
                {isFa ? "تولید و تست در شل..." : "Executing & Testing..."}
              </>
            ) : (
              <>
                <span>🚀</span>
                {isFa ? "ساخت و اجرای پروژه" : "Build & Run Project"}
              </>
            )}
          </button>

          <button className="btn-icon" onClick={() => setShowSettingsModal(true)} title={isFa ? "تنظیمات" : "Settings"}>
            ⚙️
          </button>
          <button className="btn-icon danger" onClick={handleDelete} title={isFa ? "حذف پروژه" : "Delete Project"}>
            🗑️
          </button>
        </div>
      </header>

      {/* 2. REAL TASK PIPELINE */}
      <section className="pipeline-container">
        <div className="pipeline-header-bar">
          <div className="pipeline-title-group">
            <span className="pipeline-indicator-dot"></span>
            <span className="pipeline-title">
              {isFa ? "پایپ‌لاین وظایف و وضعیت اجرا" : "Task Execution Pipeline"}
            </span>
          </div>
          <span className="pipeline-badge">
            {tasks.length} {isFa ? "تسک ثبت‌شده" : "Tasks Registered"}
          </span>
        </div>

        <div className="pipeline-scroll-track">
          {tasks.length === 0 ? (
            <div style={{ padding: "0.75rem 1rem", color: "#94A3B8", fontSize: "0.85rem" }}>
              {isFa ? "هنوز تسکی در این پروژه ثبت نشده است." : "No tasks created for this project yet."}
            </div>
          ) : (
            tasks.map((task, index) => {
              const isActive = task.status === "running";
              const isCompleted = task.status === "completed";
              const isFailed = task.status === "failed";

              return (
                <React.Fragment key={task.id}>
                  <div
                    className={`pipeline-node ${isActive ? "active" : ""} ${isCompleted ? "completed" : ""} ${isFailed ? "failed" : ""}`}
                    title={`${task.title} (${task.status})`}
                  >
                    <div className="node-avatar-wrapper">
                      <span className="node-badge">
                        {isCompleted ? "✓" : isFailed ? "✗" : isActive ? "⚡" : "⏳"}
                      </span>
                    </div>
                    <div className="node-info">
                      <span className="node-codename">{task.title.slice(0, 24)}</span>
                      <span className="node-role">{task.status}</span>
                    </div>
                  </div>

                  {index < tasks.length - 1 && (
                    <div className={`pipeline-connector ${isCompleted ? "active" : ""}`}>
                      <span className="connector-line"></span>
                      <span className="connector-arrow">➔</span>
                    </div>
                  )}
                </React.Fragment>
              );
            })
          )}
        </div>
      </section>

      {/* 3. SPLIT WORKSPACE: LEFT = ASSISTANT CHAT, RIGHT = FILES & TOOLS */}
      <main className="studio-main">
        {/* LEFT COLUMN: ASSISTANT CHAT */}
        <section className="studio-chat-pane">
          <div className="chat-header">
            <div className="hermes-badge">
              <span className="hermes-avatar">⚡</span>
              <div>
                <h4>{isFa ? "دستیار فنی نکسوس‌فورج" : "NexusForge Assistant"}</h4>
                <p>{isFa ? "راهنمای معماری و مدیریت فضای کاری پروژه" : "Technical Assistant & Workspace Liaison"}</p>
              </div>
            </div>
            <button className="btn-refresh-chat" onClick={fetchProjectData} title={isFa ? "بروزرسانی چت" : "Refresh Chat"}>
              🔄
            </button>
          </div>

          <div className="chat-messages-scroll">
            {messages
              .filter((msg): msg is ProjectMessage => Boolean(msg && msg.id && msg.sender))
              .map((msg) => (
              <div key={msg.id} className={`message-bubble ${msg.sender || "system"}`}>
                <div className="message-header">
                  <span className="message-sender-name">
                    {msg.sender === "hermes" ? (isFa ? "دستیار نکسوس‌فورج" : "NexusForge Assistant") : (isFa ? "شما" : "You")}
                  </span>
                  <span className="message-time">
                    {msg.created_at ? new Date(msg.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : ""}
                  </span>
                </div>

                {renderMessageContent(msg)}

                {/* Quick Action Suggestion Chips */}
                {msg.metadata?.quick_chips && msg.metadata.quick_chips.length > 0 && (
                  <div className="quick-chips-row">
                    {msg.metadata.quick_chips.map((chip: string, cIdx: number) => (
                      <button
                        key={cIdx}
                        className="chip-btn"
                        onClick={() => handleSendMessage(chip)}
                        disabled={isSending || isRunning}
                      >
                        {chip}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {isSending && (
              <div className="message-bubble hermes typing">
                <span className="typing-dot"></span>
                <span className="typing-dot"></span>
                <span className="typing-dot"></span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input-bar">
            <input
              type="text"
              className="chat-input"
              placeholder={isFa ? "با دستیار گفتگو کنید یا تسک جدیدی بخواهید (Enter برای ارسال)..." : "Message assistant or request changes (Enter to send)..."}
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              disabled={isSending}
            />
            <button
              className="btn-send"
              onClick={() => handleSendMessage()}
              disabled={isSending || !chatInput.trim()}
            >
              ➤
            </button>
          </div>
        </section>

        {/* RIGHT COLUMN: WORKSPACE FILES & REAL TOOLS */}
        <section className="studio-workspace-pane">
          <div className="workspace-tabs-bar">
            <div className="tab-buttons">
              <button
                className={`tab-btn ${activeTab === "files" ? "active" : ""}`}
                onClick={() => setActiveTab("files")}
              >
                📁 {isFa ? "فایل‌های پروژه" : "Project Files"} ({files.length})
              </button>
              <button
                className={`tab-btn ${activeTab === "traces" ? "active" : ""}`}
                onClick={() => setActiveTab("traces")}
              >
                🧠 {isFa ? "ردپای تفکر ۱۲ ایجنت" : "Agent Reasoning Traces"}
              </button>
              <button
                className={`tab-btn ${activeTab === "terminal" ? "active" : ""}`}
                onClick={() => setActiveTab("terminal")}
              >
                ⚡ {isFa ? "ترمینال شل" : "Live Terminal"}
              </button>
              <button
                className={`tab-btn ${activeTab === "models" ? "active" : ""}`}
                onClick={() => setActiveTab("models")}
              >
                🤖 {isFa ? "تیم ۱۲ ایجنتی و مدل‌ها" : "12-Agent Squad"}
              </button>
            </div>
            <button className="btn-refresh-files" onClick={refreshFiles} title={isFa ? "بروزرسانی فایل‌ها" : "Refresh Files"}>
              🔄
            </button>
          </div>

          <div className="workspace-tab-content">
            {/* 1. FILES & CODE VIEWER */}
            {activeTab === "files" && (
              <div className="files-layout">
                {files.length === 0 ? (
                  <div className="empty-files-placeholder">
                    <span className="empty-icon">📁</span>
                    <h4>{isFa ? "هنوز کدی در پوشه کاری تولید نشده است" : "No Code Generated Yet"}</h4>
                    <p>{isFa ? "روی دکمه «🚀 ساخت و اجرای پروژه» کلیک کنید تا تیم ۱۲ ایجنتی فایل‌ها را در ورک‌اسپیس ایجاد کند." : "Click 'Build & Run Project' to synthesize all files."}</p>
                    <button className="btn-primary-mini" onClick={handleTriggerBuild}>
                      🚀 {isFa ? "شروع ساخت کدهای واقعی با ۱۲ ایجنت" : "Start 12-Agent Synthesis"}
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="file-tree-sidebar">
                      <div className="file-tree-header">
                        <span>{isFa ? "فهرست فایل‌ها" : "Files"}</span>
                        <span className="files-count">{files.length}</span>
                      </div>
                      <div className="file-list">
                        {files.map((file) => (
                          <div
                            key={file.path}
                            className={`file-item ${selectedFile === file.path ? "active" : ""}`}
                            onClick={() => handleSelectFile(file.path)}
                          >
                            <span className="file-icon">
                              {file.name.endsWith(".py") ? "🐍" : file.name.endsWith(".html") ? "🌐" : file.name.endsWith(".json") ? "📋" : file.name.endsWith(".md") ? "📝" : "📄"}
                            </span>
                            <span className="file-name">{file.name}</span>
                            <span className="file-size">{(file.size / 1024).toFixed(1)}k</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="code-viewer-main">
                      <div className="code-viewer-header">
                        <span className="viewer-file-name">
                          📄 {selectedFile || "Select a file"}
                        </span>
                        <div className="viewer-actions">
                          <button className="btn-copy" onClick={handleCopyCode}>
                            {copied ? (isFa ? "✓ کپی شد" : "✓ Copied") : (isFa ? "📋 کپی کد" : "📋 Copy Code")}
                          </button>
                        </div>
                      </div>
                      <div className="code-viewer-body">
                        {fileLoading ? (
                          <div className="code-loading">{isFa ? "در حال بارگذاری فایل..." : "Loading..."}</div>
                        ) : (
                          <pre className="code-pre">
                            <code>{fileContent}</code>
                          </pre>
                        )}
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}

            {/* 2. REASONING TRACES */}
            {activeTab === "traces" && (
              <div className="traces-container">
                <div className="traces-header-banner">
                  <h4>🧠 {isFa ? "لاگ تحلیلی اجرای تسک‌ها" : "Task Execution Traces"}</h4>
                  <p>
                    {isFa
                      ? "ردیابی دقیق و گام‌به‌گام مراحل تحلیل و اجرای تسک‌ها در ورکر."
                      : "Detailed trace logs captured during task execution by worker nodes."}
                  </p>
                </div>

                <div className="traces-list">
                  {traces.length === 0 ? (
                    <div style={{ padding: "3rem", textAlign: "center", color: "#94A3B8" }}>
                      <p>{isFa ? "هنوز لاگ اجرایی برای این پروژه ثبت نشده است." : "No execution traces recorded yet."}</p>
                    </div>
                  ) : (
                    traces.map((tItem: any, idx: number) => {
                      const name = tItem.agent_name || tItem.role || "Worker Agent";
                      const badge = tItem.badge || "⚡";
                      const duration = tItem.duration ? `${tItem.duration}s` : "";
                      const thoughts = tItem.thoughts || [];

                      return (
                        <div key={idx} className="trace-card">
                          <div className="trace-card-top">
                            <div className="trace-agent-identity">
                              <span className="trace-badge">{badge}</span>
                              <span className="trace-name">{name}</span>
                              {duration && <span className="trace-duration">⏱ {duration}</span>}
                            </div>
                            {tItem.model && <span className="trace-model-pill">{tItem.model}</span>}
                          </div>

                          {thoughts.length > 0 && (
                            <div className="trace-thoughts">
                              <span className="trace-label">{isFa ? "تحلیل و مراحل اجرا:" : "Execution Steps:"}</span>
                              <ul>
                                {thoughts.map((th: string, tIdx: number) => (
                                  <li key={tIdx}>{th}</li>
                                ))}
                              </ul>
                            </div>
                          )}

                          <div className="trace-verdict">
                            <span className="verdict-tag">{tItem.status || "Completed"}</span>
                            {tItem.output_title && <span className="verdict-desc">{tItem.output_title}</span>}
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            )}

            {/* 3. LIVE TERMINAL */}
            {activeTab === "terminal" && (
              <div className="terminal-container">
                <div className="terminal-presets">
                  <span className="preset-label">{isFa ? "اطلاعیه امنیتی:" : "Security Notice:"}</span>
                </div>
                <div className="terminal-output-box">
                  <pre style={{ color: "#F87171" }}>
                    {isFa
                      ? "$ دسترسی مستقیم به ترمینال شل میزبان به دلایل امنیتی غیرفعال است.\n$ اجرای دستورات صرفاً از طریق ورکرها در کانتینرهای ایزوله مجاز می‌باشد."
                      : "$ Direct host terminal execution is permanently disabled for security.\n$ Subprocess execution is restricted to isolated worker containers."}
                  </pre>
                </div>
              </div>
            )}

            {/* 4. PROJECT METADATA & CONFIGURATION */}
            {activeTab === "models" && (
              <div className="models-container">
                <div className="models-info-banner">
                  <h4>⚙️ {isFa ? "مشخصات و پیکربندی پروژه" : "Project Configuration & Metadata"}</h4>
                  <p>
                    {isFa
                      ? "اطلاعات پایه‌ای فضای کاری، مدل و تنظیمات ثبت‌شده در دیتابیس."
                      : "Core workspace directory, provider settings, and metadata recorded in the database."}
                  </p>
                </div>

                <div className="models-grid">
                  <div className="model-agent-card">
                    <div className="card-top">
                      <span className="agent-badge-name">📁 {isFa ? "پوشه کاری پروژه" : "Workspace Path"}</span>
                    </div>
                    <div className="model-code-box">
                      <code>{project?.workspace_path || `workspaces/${project?.id}`}</code>
                    </div>
                    <p className="model-desc">{isFa ? "مسیر فایل‌های واقعی تولید شده روی دیسک" : "Canonical directory on filesystem for project artifacts."}</p>
                  </div>

                  <div className="model-agent-card">
                    <div className="card-top">
                      <span className="agent-badge-name">🤖 {isFa ? "تأمین‌کننده مدل" : "AI Provider"}</span>
                    </div>
                    <div className="model-code-box">
                      <code>{project?.ai_provider || "Standard Runtime"}</code>
                    </div>
                    <p className="model-desc">{isFa ? "سرویس یا مدل انتخابی برای تحلیل و هدایت" : "Configured LLM inference backend."}</p>
                  </div>

                  <div className="model-agent-card">
                    <div className="card-top">
                      <span className="agent-badge-name">🌐 {isFa ? "زبان پیش‌فرض" : "Language Setting"}</span>
                    </div>
                    <div className="model-code-box">
                      <code>{project?.preferred_language || "fa"}</code>
                    </div>
                    <p className="model-desc">{isFa ? "زبان پیش‌فرض ارتباطات و مستندات" : "Primary language for deliverables and interaction."}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>
      </main>

      {/* SETTINGS MODAL */}
      {showSettingsModal && (
        <div className="modal-overlay" onClick={() => setShowSettingsModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>⚙️ {isFa ? "تنظیمات پوشه کاری پروژه" : "Project Workspace Settings"}</h3>
            <p className="modal-desc">
              {isFa
                ? "می‌توانید مسیر پوشه کاری را در رایانه خود تغییر دهید. تمام کدهای تولیدشده در این مسیر قرار می‌گیرند."
                : "Customize the local workspace directory where all code and deliverables are written."}
            </p>
            <div className="input-group">
              <label>{isFa ? "مسیر پوشه کاری:" : "Workspace Path:"}</label>
              <input
                type="text"
                className="modal-input"
                value={editWsPath}
                onChange={(e) => setEditWsPath(e.target.value)}
                placeholder="workspaces/my_project"
              />
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowSettingsModal(false)}>
                {isFa ? "انصراف" : "Cancel"}
              </button>
              <button className="btn-primary" onClick={handleSaveSettings}>
                {isFa ? "ذخیره تغییرات" : "Save Changes"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectDetail;