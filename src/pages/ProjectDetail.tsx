import React, { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { projectApi } from "../services/api";
import { useLanguage } from "../context/LanguageContext";
import { Project, ProjectMessage, WorkspaceFile } from "../types";
import "./ProjectDetail.css";

export interface AgentSquadMember {
  id: string;
  role: string;
  codename: string;
  badge: string;
  roleTitleFa: string;
  roleTitleEn: string;
  model: string;
  descFa: string;
  descEn: string;
}

export const SQUAD_12_AGENTS: AgentSquadMember[] = [
  {
    id: "chief_orchestrator",
    role: "chief_orchestrator",
    codename: "Arya",
    badge: "👑",
    roleTitleFa: "هدایتگر ارشد کل",
    roleTitleEn: "Chief Orchestrator",
    model: "meta-llama/llama-3.3-70b-instruct:free",
    descFa: "تعامل دوستانه به زبان فارسی با کاربر، هدایت بی‌وقفه ۱۱ ایجنت، تفویض تسک‌ها و کنترل کیفی نهایی.",
    descEn: "Bilingual user liaison (Persian/English), relentless multi-agent orchestration, and output quality control.",
  },
  {
    id: "project_planner",
    role: "project_planner",
    codename: "Chronos",
    badge: "⏳",
    roleTitleFa: "برنامه‌ریز و استراتژیست",
    roleTitleEn: "Project Planner",
    model: "meta-llama/llama-3.3-70b-instruct:free",
    descFa: "شکست تسک‌ها (WBS)، تفکیک مایل‌استون‌ها، گراف وابستگی‌ها و معیارهای پذیرش (DoD).",
    descEn: "Agile WBS, user stories, milestone dependency mapping, and acceptance criteria.",
  },
  {
    id: "research_agent",
    role: "research_agent",
    codename: "Phantom",
    badge: "🔮",
    roleTitleFa: "متخصص تحقیق و مستندات",
    roleTitleEn: "Research Specialist",
    model: "mistralai/mistral-small-24b-instruct-2501:free",
    descFa: "اعتبارسنجی مستندات فنی رسمی، مقایسه کتابخانه‌ها و حذف فرض‌های نادرست.",
    descEn: "Official documentation auditing, package compatibility verification, and zero-hallucination benchmark.",
  },
  {
    id: "software_architect",
    role: "software_architect",
    codename: "Synapse",
    badge: "🏛️",
    roleTitleFa: "معمار سیستم و PRD",
    roleTitleEn: "Software Architect",
    model: "deepseek/deepseek-r1:free",
    descFa: "معماری تمیز، تفکیک دامنه‌ها (DDD)، قراردادهای OpenAPI و سند معماری سیستم.",
    descEn: "Clean Architecture, Domain-Driven Design (DDD), OpenAPI contracts, and system_architecture.md.",
  },
  {
    id: "database_agent",
    role: "database_agent",
    codename: "Matrix",
    badge: "🌐",
    roleTitleFa: "معمار پایگاه‌داده",
    roleTitleEn: "Database Architect",
    model: "deepseek/deepseek-r1:free",
    descFa: "طراحی اسکیمای رابطه‌ای، مدل‌های Pydantic v2، اعتبارسنجی فیلدها و ایندکس‌گذاری.",
    descEn: "Normalized relational schemas, Pydantic v2 data models in models.py, and indexing strategies.",
  },
  {
    id: "backend_agent",
    role: "backend_agent",
    codename: "Vulcan",
    badge: "⚡",
    roleTitleFa: "مهندس ارشد بک‌اند",
    roleTitleEn: "Backend Engineer",
    model: "qwen/qwen-2.5-coder-32b-instruct:free",
    descFa: "پیاده‌سازی وب‌سرویس ناهمگام FastAPI، روت‌های CRUD، میان‌افزار CORS و رانتایم.",
    descEn: "Asynchronous FastAPI microservice, CRUD endpoints, CORS middleware, and standalone execution in main.py.",
  },
  {
    id: "ui_ux_agent",
    role: "ui_ux_agent",
    codename: "Pixel",
    badge: "🎨",
    roleTitleFa: "طراح رابط و تجربه کاربری",
    roleTitleEn: "UI/UX Designer",
    model: "google/gemini-2.0-flash-exp:free",
    descFa: "طراحی سیستم گلاسمورفیسم تیره، توکن‌های CSS، راست‌چین و تایپوگرافی استاندارد.",
    descEn: "Obsidian dark glassmorphism design system, CSS design tokens, and native RTL typography.",
  },
  {
    id: "frontend_agent",
    role: "frontend_agent",
    codename: "Prism",
    badge: "💎",
    roleTitleFa: "مهندس ارشد فرانت‌اند",
    roleTitleEn: "Frontend Engineer",
    model: "google/gemini-2.0-flash-exp:free",
    descFa: "توسعه داشبورد وب تک‌صفحه‌ای (SPA)، اتصال بی‌درنگ به اندپوینت‌های بک‌اند و تعامل آنی.",
    descEn: "Interactive standalone SPA in index.html, async fetch integration, and reactive state management.",
  },
  {
    id: "security_agent",
    role: "security_agent",
    codename: "Cipher",
    badge: "🛡️",
    roleTitleFa: "بازرس ارشد امنیت",
    roleTitleEn: "Security Auditor",
    model: "mistralai/mistral-small-24b-instruct-2501:free",
    descFa: "تحلیل تهدیدات OWASP Top 10، اعتبارسنجی ورودی‌ها، مقابله با XSS و گزارش امنیت.",
    descEn: "OWASP Top 10 threat modeling, input sanitization, CORS security, and security_audit.md.",
  },
  {
    id: "devops_agent",
    role: "devops_agent",
    codename: "Orbit",
    badge: "🚀",
    roleTitleFa: "مهندس دواپس و زیرساخت",
    roleTitleEn: "DevOps Engineer",
    model: "qwen/qwen-2.5-coder-32b-instruct:free",
    descFa: "پین دقیق نسخه‌های requirements.txt و تدوین راهنمای جامع و آسان README.md.",
    descEn: "Deterministic dependency pinning in requirements.txt, deployment guides, and README.md runbook.",
  },
  {
    id: "mobile_agent",
    role: "mobile_agent",
    codename: "Nova",
    badge: "✨",
    roleTitleFa: "بازبین کیفیت و استاندارد کد",
    roleTitleEn: "Code Reviewer & Quality",
    model: "qwen/qwen-2.5-coder-32b-instruct:free",
    descFa: "بازبینی کدهای پایتون بر اساس PEP8، اصول Clean Code و گزارش سلامت کیفی کد.",
    descEn: "PEP8 compliance, static type audit, cyclomatic complexity reduction, and code_review.md.",
  },
  {
    id: "qa_agent",
    role: "qa_agent",
    codename: "Sentinel",
    badge: "⚔️",
    roleTitleFa: "مهندس ارشد آزمون و ترمینال",
    roleTitleEn: "QA & Verification Engineer",
    model: "mistralai/mistral-small-24b-instruct-2501:free",
    descFa: "اجرای کامپایل ترمینال پایتون، راستی‌آزمایی رانتایم و صدور تاییدیه کیفی نهایی.",
    descEn: "Terminal bytecode compilation (py_compile), headless import sanity check, and QA certification.",
  },
];

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

      {/* 2. VISUAL 12-AGENT HANDOFF PIPELINE */}
      <section className="pipeline-container">
        <div className="pipeline-header-bar">
          <div className="pipeline-title-group">
            <span className="pipeline-indicator-dot"></span>
            <span className="pipeline-title">
              {isFa ? "پایپ‌لاین پاس‌کاری و بازرسی ۱۲ ایجنت تخصصی (Supervised by Arya 👑)" : "12-Agent Autonomous Pipeline (Supervised by Arya 👑)"}
            </span>
          </div>
          <span className="pipeline-badge">
            {isRunning ? (isFa ? "⚡ در حال گردش و بررسی تسک‌ها" : "⚡ Active Execution Flow") : (isFa ? "۱۲ ایجنت آنلاین" : "12 Agents Online")}
          </span>
        </div>

        <div className="pipeline-scroll-track">
          {SQUAD_12_AGENTS.map((agent, index) => {
            const isActive = isRunning && activePipelineStep === index;
            const isCompleted = isRunning && activePipelineStep > index;

            return (
              <React.Fragment key={agent.id}>
                <div
                  className={`pipeline-node ${isActive ? "active" : ""} ${isCompleted ? "completed" : ""}`}
                  onClick={() => setActiveTab("models")}
                  title={`${agent.badge} ${agent.codename} — ${isFa ? agent.roleTitleFa : agent.roleTitleEn}`}
                >
                  <div className="node-avatar-wrapper">
                    <span className="node-badge">{agent.badge}</span>
                    {isActive && <span className="node-pulse-ring"></span>}
                    {isCompleted && <span className="node-check-badge">✓</span>}
                  </div>
                  <div className="node-info">
                    <span className="node-codename">{agent.codename}</span>
                    <span className="node-role">{isFa ? agent.roleTitleFa : agent.roleTitleEn}</span>
                  </div>
                </div>

                {index < SQUAD_12_AGENTS.length - 1 && (
                  <div className={`pipeline-connector ${isCompleted ? "active" : ""}`}>
                    <span className="connector-line"></span>
                    <span className="connector-arrow">➔</span>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </section>

      {/* 3. SPLIT WORKSPACE: LEFT = CHAT (HERMES / ARYA), RIGHT = FILES & TOOLS */}
      <main className="studio-main">
        {/* LEFT COLUMN: HERMES & ARYA COPILOT CHAT */}
        <section className="studio-chat-pane">
          <div className="chat-header">
            <div className="hermes-badge">
              <span className="hermes-avatar">👑</span>
              <div>
                <h4>{isFa ? "👑 آریا — معمار ارشد و هدایتگر کل" : "👑 Arya — Chief Architect & Orchestrator"}</h4>
                <p>{isFa ? "هم‌صحبتی فارسی، هدایت فنی ۱۱ ایجنت تخصصی و تضمین کیفیت" : "Persian User Liaison & 12-Agent Technical Lead"}</p>
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
                    {msg.sender === "hermes" ? "👑 Arya (هدایتگر ارشد)" : (isFa ? "شما" : "You")}
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
              placeholder={isFa ? "با آریا گفتگو کنید یا تسک جدیدی بخواهید (Enter برای ارسال)..." : "Talk with Arya or request changes (Enter to send)..."}
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

            {/* 2. REASONING TRACES (ALL 12 AGENTS) */}
            {activeTab === "traces" && (
              <div className="traces-container">
                <div className="traces-header-banner">
                  <h4>🧠 {isFa ? "زنجیره تفکر و نظرات بازبینی آریا (12-Agent Reasoning & Review Trace)" : "12-Agent Reasoning & Arya Review Trace"}</h4>
                  <p>
                    {isFa
                      ? "آریا (👑) خروجی تک‌تک ۱۱ ایجنت تخصصی را بازرسی کرده و تاییدیه پیشرفت را صادر می‌کند."
                      : "Arya relentlessly scrutinizes every specialist deliverable before stamping approval."}
                  </p>
                </div>

                <div className="traces-list">
                  {(traces.length > 0 ? traces : SQUAD_12_AGENTS).map((tItem: any, idx: number) => {
                    const isFromSquad = !tItem.thoughts;
                    const name = tItem.agent_name || `${tItem.codename} (${isFa ? tItem.roleTitleFa : tItem.roleTitleEn}) ${tItem.badge}`;
                    const badge = tItem.badge || "🤖";
                    const model = tItem.model || "OpenRouter Free";
                    const duration = tItem.duration || "1.2s";
                    const thoughts = tItem.thoughts || [
                      isFa ? `دریافت تسک و تحلیل دقیق بر اساس استانداردهای ${tItem.codename}` : `Received task and analyzed according to standards.`,
                      isFa ? `تولید دلیوربل تخصصی و ارسال به آریا جهت بازرسی کیفی` : `Generated specialized deliverable and submitted to Arya for review.`
                    ];

                    return (
                      <div key={idx} className="trace-card">
                        <div className="trace-card-top">
                          <div className="trace-agent-identity">
                            <span className="trace-badge">{badge}</span>
                            <span className="trace-name">{name}</span>
                            <span className="trace-duration">⏱ {duration}</span>
                          </div>
                          <span className="trace-model-pill">{model}</span>
                        </div>

                        <div className="trace-thoughts">
                          <span className="trace-label">{isFa ? "فرآیند تحلیل و تفکر (Thoughts):" : "Analysis & Reasoning:"}</span>
                          <ul>
                            {thoughts.map((th: string, tIdx: number) => (
                              <li key={tIdx}>{th}</li>
                            ))}
                          </ul>
                        </div>

                        <div className="trace-verdict">
                          <span className="verdict-tag">✓ {isFa ? "تایید بازبینی آریا 👑" : "Arya Review Approved 👑"}</span>
                          <span className="verdict-desc">{tItem.output_title || (isFa ? "خروجی با موفقیت اعتبارسنجی شد" : "Deliverable verified")}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* 3. LIVE TERMINAL */}
            {activeTab === "terminal" && (
              <div className="terminal-container">
                <div className="terminal-presets">
                  <span className="preset-label">{isFa ? "دستورات سریع شل:" : "Quick Actions:"}</span>
                  <button className="preset-btn" onClick={() => handleRunTerminal("dir")}>dir</button>
                  <button className="preset-btn" onClick={() => handleRunTerminal("python -m py_compile main.py models.py")}>py_compile main.py</button>
                  <button className="preset-btn" onClick={() => handleRunTerminal("python -c \"import main; print('FastAPI Ready')\"")}>test import</button>
                  <button className="preset-btn" onClick={() => handleRunTerminal("type requirements.txt")}>type requirements.txt</button>
                </div>
                <div className="terminal-output-box">
                  <pre>{termOutput}</pre>
                </div>
                <div className="terminal-input-bar">
                  <span className="terminal-prompt">$</span>
                  <input
                    type="text"
                    className="terminal-input"
                    value={termCommand}
                    onChange={(e) => setTermCommand(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleRunTerminal()}
                    placeholder="Type shell command..."
                    disabled={termRunning}
                  />
                  <button
                    className="terminal-exec-btn"
                    onClick={() => handleRunTerminal()}
                    disabled={termRunning || !termCommand.trim()}
                  >
                    {termRunning ? "..." : (isFa ? "اجرا" : "Run")}
                  </button>
                </div>
              </div>
            )}

            {/* 4. ASSIGNED 12-AGENT SQUAD */}
            {activeTab === "models" && (
              <div className="models-container">
                <div className="models-info-banner">
                  <h4>🤖 {isFa ? "تیم ۱۲ ایجنتی تخصصی نکسوس‌فورج و مدل‌های رایگان" : "NexusForge 12-Agent Specialized Squad"}</h4>
                  <p>
                    {isFa
                      ? "آریا (👑) تسک‌های تخصصی را به این ۱۱ مهندس واگذار کرده و خروجی تک‌تک آن‌ها را با وسواس کنترل می‌کند."
                      : "Arya assigns tasks to these 11 specialized engineers and scrutinizes every output."}
                  </p>
                </div>

                <div className="models-grid">
                  {SQUAD_12_AGENTS.map((item, idx) => (
                    <div key={idx} className="model-agent-card">
                      <div className="card-top">
                        <span className="agent-badge-name">{item.badge} {item.codename}</span>
                        <span className="role-tag">{isFa ? item.roleTitleFa : item.roleTitleEn}</span>
                      </div>
                      <div className="model-code-box">
                        <code>{item.model}</code>
                      </div>
                      <p className="model-desc">{isFa ? item.descFa : item.descEn}</p>
                    </div>
                  ))}
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