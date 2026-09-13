import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useLanguage } from "../context/LanguageContext";

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
  disabled?: boolean;
}

const Navigation: React.FC = () => {
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);
  const { t, lang, toggleLang, isRTL } = useLanguage();

  const navItems: NavItem[] = [
    {
      label: t("nav.dashboard"),
      path: "/",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="3" width="7" height="9"></rect>
          <rect x="14" y="3" width="7" height="5"></rect>
          <rect x="14" y="12" width="7" height="9"></rect>
          <rect x="3" y="16" width="7" height="5"></rect>
        </svg>
      ),
    },
    {
      label: t("nav.projects"),
      path: "/projects",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
        </svg>
      ),
    },
    {
      label: t("nav.workers"),
      path: "/workers",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="6" cy="6" r="2"></circle>
          <circle cx="6" cy="18" r="2"></circle>
          <circle cx="18" cy="12" r="2"></circle>
          <path d="M8 6h6a2 2 0 0 1 2 2v2"></path>
          <path d="M8 18h6a2 2 0 0 0 2-2v-2"></path>
          <path d="M14 12h4"></path>
        </svg>
      ),
    },
    {
      label: t("nav.activity"),
      path: "/activity",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
        </svg>
      ),
    },
    {
      label: t("nav.agents"),
      path: "/agents",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
          <circle cx="9" cy="7" r="4"></circle>
          <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
          <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
        </svg>
      ),
    },
    {
      label: t("nav.settings"),
      path: "/settings",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="3"></circle>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
        </svg>
      ),
    },
  ];

  const handleLinkClick = () => {
    setIsOpen(false);
  };

  return (
    <>
      {/* Mobile Toggle Button */}
      <button
        type="button"
        className="navigation__mobile-toggle"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label={isOpen ? "Close navigation menu" : "Open navigation menu"}
        aria-expanded={isOpen}
      >
        {isOpen ? (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        ) : (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        )}
      </button>

      {/* Backdrop Overlay for Mobile */}
      {isOpen && (
        <div
          className="navigation__overlay"
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Drawer / Sidebar Navigation */}
      <nav className={`navigation ${isOpen ? "navigation--open" : ""}`} aria-label="Main navigation">
        <div className="navigation__logo">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#007BFF" strokeWidth="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
            <path d="M2 17l10 5 10-5"></path>
            <path d="M2 12l10 5 10-5"></path>
          </svg>
          <span className="navigation__logo-text">NexusForge</span>
        </div>

        <ul className="navigation__items">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            const isDisabled = item.disabled;

            return (
              <li key={item.path} className="navigation__item">
                {isDisabled ? (
                  <span className="navigation__link navigation__link--disabled" title="Coming in a future phase">
                    <span className="navigation__icon">{item.icon}</span>
                    <span className="navigation__label">{item.label}</span>
                  </span>
                ) : (
                  <Link
                    to={item.path}
                    className={`navigation__link ${isActive ? "navigation__link--active" : ""}`}
                    aria-current={isActive ? "page" : undefined}
                    onClick={handleLinkClick}
                  >
                    <span className="navigation__icon">{item.icon}</span>
                    <span className="navigation__label">{item.label}</span>
                  </Link>
                )}
              </li>
            );
          })}
        </ul>

        <div className="navigation__footer">
          {/* Language Switcher */}
          <div className="navigation__lang-toggle-wrapper" style={{ marginBottom: "12px" }}>
            <button
              type="button"
              className="navigation__lang-btn"
              onClick={toggleLang}
              style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "8px 12px",
                background: "rgba(255, 255, 255, 0.05)",
                border: "1px solid rgba(255, 255, 255, 0.12)",
                borderRadius: "8px",
                color: "var(--color-text-primary, #F0F4F8)",
                cursor: "pointer",
                fontSize: "0.85rem",
                transition: "all 0.2s ease",
              }}
              title={lang === "fa" ? "Switch to English" : "تغییر به زبان فارسی"}
            >
              <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <span>{lang === "fa" ? "🇮🇷" : "🇬🇧"}</span>
                <span style={{ fontWeight: 500 }}>{lang === "fa" ? "زبان: فارسی" : "Language: English"}</span>
              </span>
              <span
                style={{
                  fontSize: "0.7rem",
                  padding: "2px 6px",
                  borderRadius: "4px",
                  background: "var(--color-primary, #007BFF)",
                  color: "#fff",
                  fontWeight: 600,
                }}
              >
                {lang.toUpperCase()}
              </span>
            </button>
          </div>

          <div className="navigation__user-profile">
            <div className="navigation__user-avatar">
              {(localStorage.getItem("user_email") || "O").charAt(0).toUpperCase()}
            </div>
            <div className="navigation__user-details">
              <span className="navigation__user-email">{localStorage.getItem("user_email") || "Operator"}</span>
              <span className="navigation__user-role">{t("nav.user")}</span>
            </div>
            <button
              className="navigation__logout-btn"
              onClick={() => {
                localStorage.removeItem("token");
                localStorage.removeItem("user_email");
                window.location.href = "/login";
              }}
              title="Sign Out"
              aria-label="Sign Out"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                <polyline points="16 17 21 12 16 7"></polyline>
                <line x1="21" y1="12" x2="9" y2="12"></line>
              </svg>
            </button>
          </div>

          <div className="navigation__system-status-row">
            <div className="navigation__status">
              <span className="status-dot status-dot--online"></span>
              <span className="navigation__status-text">System Online</span>
            </div>
            <span className="navigation__version">v0.1.0</span>
          </div>
        </div>
      </nav>
    </>
  );
};

export default Navigation;