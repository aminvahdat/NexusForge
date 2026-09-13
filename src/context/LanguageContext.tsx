import React, { createContext, useContext, useState, useEffect } from "react";

export type Language = "fa" | "en";

interface LanguageContextType {
  lang: Language;
  setLang: (lang: Language) => void;
  toggleLang: () => void;
  isRTL: boolean;
  t: (key: string, fallback?: string) => string;
}

const translations: Record<Language, Record<string, string>> = {
  fa: {
    // Navigation
    "nav.dashboard": "داشبورد",
    "nav.projects": "پروژه‌ها",
    "nav.workers": "کارگرها",
    "nav.activity": "فعالیت زنده",
    "nav.agents": "تیم ایجنت‌ها",
    "nav.settings": "تنظیمات هوش مصنوعی",
    "nav.logout": "خروج",
    "nav.user": "کاربر ادمین",

    // Dashboard Hero & Autonomous Prompt
    "hero.tagline": "ایده از شما، ساخت خودکار از نکسوس‌فورج",
    "hero.subtitle": "فقط هدف یا نیاز نرم‌افزاری خود را توصیف کنید؛ نکسوس‌فورج معماری و اجرای واقعی تسک‌ها را مدیریت می‌کند.",
    "hero.prompt_placeholder": "مثال: یک وب‌اپلیکیشن مدیریت وظایف تیمی با قابلیت چت زنده، تگ‌گذاری و احراز هویت با React و FastAPI بساز...",
    "hero.launch_btn": "🚀 پرتاب فورج خودکار",
    "hero.launching": "در حال راه‌اندازی پروژه و ساخت فضای کاری...",
    "hero.quick_prompts": "پیشنهادهای سریع:",
    "hero.quick_prompt_1": "💳 سامانه درگاه پرداخت و کیف‌پول کریپتو با اعتبارسنجی امن",
    "hero.quick_prompt_2": "📊 داشبورد تحلیل داده‌های فروش با چارت‌های زنده و وب‌سوکت",
    "hero.quick_prompt_3": "🤖 ربات هوشمند مدیریت سفارشات و تیکت‌های مشتریان",

    // Dashboard Stats
    "dash.total_projects": "کل پروژه‌ها",
    "dash.active_executions": "اجراهای فعال",
    "dash.system_health": "سلامت زیرساخت",
    "dash.online_workers": "کارگرهای آنلاین",
    "dash.healthy": "سالم و فعال",
    "dash.recent_activity": "فعالیت‌های اخیر تیم",
    "dash.no_events": "هنوز رخدادی ثبت نشده است.",
    "dash.view_all_activity": "مشاهده تمام فعالیت‌ها",
    "dash.quick_actions": "دسترسی‌های سریع",
    "dash.new_project": "پروژه جدید",
    "dash.config_api": "پیکربندی API",

    // Projects Page
    "projects.title": "مدیریت پروژه‌ها",
    "projects.subtitle": "نظارت بر پروژه‌های نرم‌افزاری و چرخه‌حیات توسعه هوشمند",
    "projects.new_btn": "پروژه جدید",
    "projects.tab_active": "پروژه‌های فعال",
    "projects.tab_archived": "بایگانی‌شده",
    "projects.tab_all": "همه پروژه‌ها",
    "projects.search_placeholder": "جستجو در میان پروژه‌ها...",
    "projects.empty_title": "پروژه‌ای یافت نشد",
    "projects.empty_desc": "اولین پروژه خود را بسازید یا از لانچر هوشمند صفحه اصلی استفاده کنید.",
    "projects.status_active": "فعال",
    "projects.status_archived": "بایگانی‌شده",
    "projects.badge_lang": "زبان:",
    "projects.badge_provider": "سرویس:",
    "projects.badge_model": "مدل:",
    "projects.created_at": "تاریخ ایجاد:",
    "projects.action_archive": "بایگانی",
    "projects.action_unarchive": "خروج از بایگانی",
    "projects.action_delete": "حذف",
    "projects.action_open": "مشاهده پروژه",
    "projects.delete_confirm_title": "آیا از حذف این پروژه اطمینان دارید؟",
    "projects.delete_confirm_desc": "با حذف پروژه، تمامی تسک‌ها و فایل‌های مرتبط با آن برای همیشه پاک خواهند شد.",

    // Project Modal
    "modal.create_project_title": "تعریف پروژه نرم‌افزاری جدید",
    "modal.project_name": "نام پروژه",
    "modal.project_desc": "توضیحات و نیازمندی‌های اصلی",
    "modal.ai_provider": "ارائه‌دهنده پیش‌فرض هوش مصنوعی",
    "modal.preferred_lang": "زبان ارتباطی ایجنت‌ها",
    "modal.cancel": "انصراف",
    "modal.submit": "ایجاد پروژه",

    // Agents
    "agents.title": "فرماندهی و پیکربندی ایجنت‌های هوشمند",
    "agents.subtitle": "سفارشی‌سازی پرامپت‌ها، سطح استدلال و هویت تیم خودمختار",
    "agents.filter_all": "همه ایجنت‌ها",
    "agents.filter_active": "فعال",
    "agents.filter_custom": "شخصی‌سازی‌شده",
    "agents.add_custom": "تعریف ایجنت جدید",
    "agents.search": "جستجوی ایجنت...",
    "agents.reasoning_intensity": "شدت استدلال:",
    "agents.customize_btn": "سفارشی‌سازی پرامپت",
    "agents.chief_tag": "فرمانده کل (تنها دریافت‌کننده تسک از کاربر)",

    // General & Actions
    "common.loading": "در حال بارگذاری...",
    "common.save": "ذخیره تغییرات",
    "common.cancel": "انصراف",
    "common.delete": "حذف",
    "common.edit": "ویرایش",
    "common.confirm": "تایید",
    "common.back": "بازگشت",
    "common.success": "عملیات با موفقیت انجام شد",
    "common.error": "خطا در انجام عملیات",
  },
  en: {
    // Navigation
    "nav.dashboard": "Dashboard",
    "nav.projects": "Projects",
    "nav.workers": "Workers",
    "nav.activity": "Live Activity",
    "nav.agents": "Agents Team",
    "nav.settings": "AI Settings",
    "nav.logout": "Logout",
    "nav.user": "Admin User",

    // Dashboard Hero & Autonomous Prompt
    "hero.tagline": "From Vision to Production — Autonomous Forge",
    "hero.subtitle": "State your goal and let NexusForge handle the technical architecture and real task execution.",
    "hero.prompt_placeholder": "E.g. Build a collaborative task board with real-time WebSockets, tags, and JWT auth using React and FastAPI...",
    "hero.launch_btn": "🚀 Launch Autonomous Forge",
    "hero.launching": "Forging project & creating workspace...",
    "hero.quick_prompts": "Quick suggestions:",
    "hero.quick_prompt_1": "💳 Crypto payment gateway & multi-sig wallet engine",
    "hero.quick_prompt_2": "📊 Real-time analytics dashboard with live websocket charts",
    "hero.quick_prompt_3": "🤖 Automated AI customer support & ticketing bot",

    // Dashboard Stats
    "dash.total_projects": "Total Projects",
    "dash.active_executions": "Active Executions",
    "dash.system_health": "System Health",
    "dash.online_workers": "Online Workers",
    "dash.healthy": "Operational",
    "dash.recent_activity": "Recent Team Activity",
    "dash.no_events": "No events recorded yet.",
    "dash.view_all_activity": "View All Activity",
    "dash.quick_actions": "Quick Actions",
    "dash.new_project": "New Project",
    "dash.config_api": "Configure API",

    // Projects Page
    "projects.title": "Projects Hub",
    "projects.subtitle": "Monitor software initiatives and autonomous lifecycle progression",
    "projects.new_btn": "New Project",
    "projects.tab_active": "Active Projects",
    "projects.tab_archived": "Archived",
    "projects.tab_all": "All Projects",
    "projects.search_placeholder": "Search projects...",
    "projects.empty_title": "No Projects Found",
    "projects.empty_desc": "Create your first project or use the autonomous launcher on the dashboard.",
    "projects.status_active": "Active",
    "projects.status_archived": "Archived",
    "projects.badge_lang": "Lang:",
    "projects.badge_provider": "Provider:",
    "projects.badge_model": "Model:",
    "projects.created_at": "Created:",
    "projects.action_archive": "Archive",
    "projects.action_unarchive": "Unarchive",
    "projects.action_delete": "Delete",
    "projects.action_open": "Open Project",
    "projects.delete_confirm_title": "Are you sure you want to delete this project?",
    "projects.delete_confirm_desc": "Deleting this project will permanently remove all tasks and associated artifacts.",

    // Project Modal
    "modal.create_project_title": "Create New Software Project",
    "modal.project_name": "Project Name",
    "modal.project_desc": "Core Description & Requirements",
    "modal.ai_provider": "Default AI Provider",
    "modal.preferred_lang": "Agent Working Language",
    "modal.cancel": "Cancel",
    "modal.submit": "Create Project",

    // Agents
    "agents.title": "Autonomous Agents Command",
    "agents.subtitle": "Customize system prompts, reasoning intensity, and autonomous role personas",
    "agents.filter_all": "All Agents",
    "agents.filter_active": "Active",
    "agents.filter_custom": "Customized",
    "agents.add_custom": "Add Custom Agent",
    "agents.search": "Search agents...",
    "agents.reasoning_intensity": "Reasoning Effort:",
    "agents.customize_btn": "Customize Prompt",
    "agents.chief_tag": "Chief Commander (Exclusive user task recipient)",

    // General & Actions
    "common.loading": "Loading...",
    "common.save": "Save Changes",
    "common.cancel": "Cancel",
    "common.delete": "Delete",
    "common.edit": "Edit",
    "common.confirm": "Confirm",
    "common.back": "Back",
    "common.success": "Operation completed successfully",
    "common.error": "Operation failed",
  },
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lang, setLangState] = useState<Language>(() => {
    const saved = localStorage.getItem("nf_lang") as Language;
    return saved === "en" || saved === "fa" ? saved : "fa"; // Default to Persian as requested
  });

  const isRTL = lang === "fa";

  useEffect(() => {
    localStorage.setItem("nf_lang", lang);
    document.documentElement.lang = lang;
    document.documentElement.dir = isRTL ? "rtl" : "ltr";
    if (isRTL) {
      document.body.classList.add("rtl-layout");
      document.body.classList.remove("ltr-layout");
    } else {
      document.body.classList.add("ltr-layout");
      document.body.classList.remove("rtl-layout");
    }
  }, [lang, isRTL]);

  const setLang = (newLang: Language) => {
    setLangState(newLang);
  };

  const toggleLang = () => {
    setLangState((prev) => (prev === "fa" ? "en" : "fa"));
  };

  const t = (key: string, fallback?: string): string => {
    return translations[lang]?.[key] || translations.en?.[key] || fallback || key;
  };

  return (
    <LanguageContext.Provider value={{ lang, setLang, toggleLang, isRTL, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = (): LanguageContextType => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }
  return context;
};
