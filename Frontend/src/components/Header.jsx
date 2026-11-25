
import React from "react";
import {
  Sun,
  Moon,
  Menu,
  Building2,
  LogOut
} from "lucide-react";

import { useAuth } from "../context/AuthContext";

export default function Header({
  theme,
  toggleTheme,
  activePage,
  sessions = [],
  activeSession,
  setActiveSession,
  setPage,
  onToggleMobileSidebar
}) {
  const { user, signOut } = useAuth();

  const pageMeta = {
    "Dashboard": {
      title: "Dashboard",
      subtitle: "Research activity, active sessions, and document processing pipeline"
    },
    "Sessions": {
      title: "Research Sessions",
      subtitle: "Manage target entity workspaces, objectives, and assigned filings"
    },
    "Research Sessions": {
      title: "Research Sessions",
      subtitle: "Manage target entity workspaces, objectives, and assigned filings"
    },
    "Documents": {
      title: "Financial Documents",
      subtitle: "Institutional filings, parsing lifecycle, and vector search index"
    },
    "Document Library": {
      title: "Financial Documents",
      subtitle: "Institutional filings, parsing lifecycle, and vector search index"
    },
    "Upload Document": {
      title: "Upload Filing",
      subtitle: "Add annual reports or 10-K filings for AI analysis"
    },
    "Research": {
      title: "AI Research",
      subtitle: "Research financial documents with source-backed answers"
    },
    "Financial Query & Research": {
      title: "AI Research",
      subtitle: "Research financial documents with source-backed answers"
    },
    "Analysis": {
      title: "Financial Analysis",
      subtitle: "Extracted statement line items, forensic red flags, and peer benchmarks"
    },
    "Financial Analysis": {
      title: "Financial Analysis",
      subtitle: "Extracted statement line items, forensic red flags, and peer benchmarks"
    },
    "Reports": {
      title: "Reports",
      subtitle: "Structured financial dossiers and executive publication-ready PDF exports"
    },
    "Research Reports": {
      title: "Reports",
      subtitle: "Structured financial dossiers and executive publication-ready PDF exports"
    },
    "Analyst Report": {
      title: "Reports",
      subtitle: "Structured financial dossiers and executive publication-ready PDF exports"
    },
    "Settings": {
      title: "System & Multi-Agent Orchestration",
      subtitle: "Execution timeline, agent states, and runtime diagnostic status"
    }
  };

  const meta = pageMeta[activePage] || {
    title: activePage,
    subtitle: "Multi-agent financial intelligence"
  };

  async function handleLogout() {
    const { error } = await signOut();

    if (error) {
      console.error("Logout failed:", error.message);
    }
  }

  const userName =
    user?.user_metadata?.full_name ||
    user?.user_metadata?.name ||
    user?.email;

  const avatarUrl = user?.user_metadata?.avatar_url;

  return (
    <header className="fin-header-wrapper fin-header-minimal">
      <div className="fin-navbar">

        {/* Left: Mobile Toggle & Page Title */}
        <div className="fin-navbar-left">
          {onToggleMobileSidebar && (
            <button
              type="button"
              className="fin-mobile-toggle-btn"
              onClick={onToggleMobileSidebar}
              aria-label="Toggle menu"
            >
              <Menu size={18} />
            </button>
          )}

          <div className="fin-title-block">
            <h1 className="fin-page-title text-base sm:text-lg font-bold">
              {meta.title}
            </h1>
            <p className="text-xs text-muted hidden sm:block">
              {meta.subtitle}
            </p>
          </div>
        </div>

        {/* Right: Company Selector, User Profile & Theme */}
        <div className="fin-navbar-right flex items-center gap-3">

          {/* Active Company Selector */}
          {sessions && sessions.length > 0 && activePage !== "Research" && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-subtle border border-subtle text-xs">
              <Building2 size={13} className="text-teal" />
              <span className="text-muted hidden md:inline font-medium">
                Focus:
              </span>

              <select
                aria-label="Current research company"
                className="fin-header-select text-xs font-semibold cursor-pointer"
                value={activeSession?.id || (sessions[0] && sessions[0].id) || ""}
                onChange={(e) => {
                  const s = sessions.find(
                    (item) => item.id === e.target.value
                  );

                  if (s && setActiveSession) {
                    setActiveSession(s);
                  }
                }}
              >
                {sessions.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.company || s.title}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Logged-in User Profile */}
          {user && (
            <div className="flex items-center gap-2">
              {avatarUrl ? (
                <img
                  src={avatarUrl}
                  alt="Profile"
                  referrerPolicy="no-referrer"
                  className="w-8 h-8 rounded-full object-cover border border-subtle"
                />
              ) : (
                <div className="w-8 h-8 rounded-full bg-subtle flex items-center justify-center text-sm font-semibold">
                  {userName?.charAt(0)?.toUpperCase() || "U"}
                </div>
              )}

              <span className="text-xs font-medium hidden lg:inline max-w-32 truncate">
                {userName}
              </span>

              <button
                type="button"
                className="fin-icon-btn p-2 rounded-lg border border-subtle hover:bg-hover transition-colors"
                onClick={handleLogout}
                title="Sign out"
                aria-label="Sign out"
              >
                <LogOut size={16} />
              </button>
            </div>
          )}

          {/* Theme Switcher */}
          <button
            type="button"
            className="fin-icon-btn p-2 rounded-lg border border-subtle hover:bg-hover transition-colors"
            onClick={toggleTheme}
            title={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
            aria-label="Toggle theme"
          >
            {theme === "dark" ? (
              <Sun size={16} className="text-warning" />
            ) : (
              <Moon size={16} className="text-muted" />
            )}
          </button>

        </div>
      </div>
    </header>
  );
}
