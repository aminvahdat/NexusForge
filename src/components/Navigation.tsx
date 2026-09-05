import React from "react";
import { Link, useLocation } from "react-router-dom";
import "./Navigation.css";

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
  disabled?: boolean;
}

const Navigation: React.FC = () => {
  const location = useLocation();

  const navItems: NavItem[] = [
    {
      label: "Dashboard",
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
      label: "Projects",
      path: "/projects",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
        </svg>
      ),
    },
    {
      label: "Tasks",
      path: "/tasks",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="8" y1="6" x2="21" y2="6"></line>
          <line x1="8" y1="12" x2="21" y2="12"></line>
          <line x1="8" y1="18" x2="13" y2="18"></line>
          <line x1="3" y1="6" x2="3.01" y2="6"></line>
          <line x1="3" y1="12" x2="3.01" y2="12"></line>
          <line x1="3" y1="18" x2="3.01" y2="18"></line>
        </svg>
      ),
      disabled: true,
    },
    {
      label: "Workers",
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
      disabled: true,
    },
    {
      label: "Activity",
      path: "/activity",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
        </svg>
      ),
      disabled: true,
    },
    {
      label: "Settings",
      path: "/settings",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="3"></circle>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
        </svg>
      ),
      disabled: true,
    },
  ];

  return (
    <nav className="navigation" aria-label="Main navigation">
      <div className="navigation__logo">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
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
        <div className="navigation__status">
          <span className="status-dot status-dot--online"></span>
          <span className="navigation__status-text">System Online</span>
        </div>
        <span className="navigation__version">v0.1.0</span>
      </div>
    </nav>
  );
};

export default Navigation;