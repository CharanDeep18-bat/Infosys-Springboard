import React from "react";
import {
  LayoutDashboard,
  Building2,
  FolderOpen,
  FileText,
  Cpu,
  Layers,
  ShieldCheck,
  AlertTriangle,
  TrendingUp,
  Search,
  ChevronLeft,
  ChevronRight
} from "lucide-react";

/**
 * Clean, production-grade financial research navigation items.
 */
export const NAVIGATION_ITEMS = [
  {
    id: "dashboard",
    label: "Dashboard",
    icon: LayoutDashboard,
    page: "Dashboard",
    matchPages: ["Dashboard"]
  },
  {
    id: "workspaces",
    label: "Workspace Management",
    icon: Building2,
    page: "Sessions",
    subview: "directory",
    matchPages: ["Workspace Directory", "workspaces"]
  },
  {
    id: "sessions",
    label: "Research Sessions",
    icon: FolderOpen,
    page: "Sessions",
    subview: "details",
    matchPages: ["Sessions", "Research Sessions", "Session Details", "Create Session"]
  },
  {
    id: "documents",
    label: "Document Library",
    icon: FileText,
    page: "Documents",
    subview: "library",
    matchPages: ["Documents", "Document Library", "Upload Document"]
  },
  {
    id: "document_processing",
    label: "Document Processing",
    icon: Cpu,
    page: "Documents",
    subview: "details",
    matchPages: ["Document Details", "Knowledge Base"]
  },
  {
    id: "extraction",
    label: "Financial Extraction",
    icon: Layers,
    page: "Analysis",
    tab: "extraction",
    matchPages: ["Extraction", "Extracted Financials"]
  },
  {
    id: "evidence",
    label: "Evidence Validation",
    icon: ShieldCheck,
    page: "Analysis",
    tab: "evidence",
    matchPages: ["Evidence Validation", "Citations"]
  },
  {
    id: "redflags",
    label: "Red Flag Analysis",
    icon: AlertTriangle,
    page: "Analysis",
    tab: "redflags",
    matchPages: ["Red Flags", "Forensic Red Flags"]
  },
  {
    id: "analysis_results",
    label: "Analysis Results",
    icon: TrendingUp,
    page: "Analysis",
    tab: "overview",
    matchPages: ["Analysis", "Financial Analysis", "Research Workspace"]
  },
  {
    id: "semantic_search",
    label: "Semantic Search",
    icon: Search,
    page: "Analysis",
    tab: "ingestion",
    matchPages: ["Semantic Search", "Vector Search"]
  }
];

export default function Sidebar({
  activePage,
  sessionSubView = "directory",
  documentSubView = "library",
  analysisTab = "extraction",
  setPage,
  collapsed,
  onToggleCollapse
}) {
  function isItemActive(item) {
    if (item.id === "dashboard") {
      return activePage === "Dashboard";
    }
    if (item.id === "workspaces") {
      return activePage === "Sessions" && sessionSubView === "directory";
    }
    if (item.id === "sessions") {
      return activePage === "Sessions" && (sessionSubView === "details" || sessionSubView === "create");
    }
    if (item.id === "documents") {
      return activePage === "Documents" && (documentSubView === "library" || documentSubView === "upload");
    }
    if (item.id === "document_processing") {
      return activePage === "Documents" && documentSubView === "details";
    }
    if (item.id === "extraction") {
      return activePage === "Analysis" && (analysisTab === "extraction" || !analysisTab);
    }
    if (item.id === "evidence") {
      return activePage === "Analysis" && analysisTab === "evidence";
    }
    if (item.id === "redflags") {
      return activePage === "Analysis" && analysisTab === "redflags";
    }
    if (item.id === "analysis_results") {
      return activePage === "Analysis" && analysisTab === "overview";
    }
    if (item.id === "semantic_search") {
      return activePage === "Analysis" && analysisTab === "ingestion";
    }
    return item.matchPages?.includes(activePage);
  }

  function handleNavigate(item) {
    if (setPage) {
      setPage(item.id, item.subview, item.tab);
    }
  }

  return (
    <aside className={`fin-sidebar ${collapsed ? "collapsed" : ""}`}>
      {/* Sleek Minimal Brand */}
      <div
        className="fin-brand"
        onClick={() => setPage && setPage("dashboard")}
        title={collapsed ? "FinResearch" : "Go to Dashboard"}
      >
        <div className="fin-brand-icon">
          <TrendingUp size={19} color="#ffffff" />
        </div>
        {!collapsed && (
          <div className="fin-brand-text">
            <h2>FinResearch</h2>
            <p>AI Financial Analyst</p>
          </div>
        )}
      </div>

      {/* Primary Clean Navigation */}
      <div className="fin-sidebar-section">
        {!collapsed && <p className="fin-menu-heading">NAVIGATION</p>}
        <nav className="fin-nav">
          {NAVIGATION_ITEMS.map((item) => {
            const IconComponent = item.icon;
            const isActive = isItemActive(item);

            return (
              <button
                key={item.id}
                type="button"
                className={`fin-nav-item ${isActive ? "active" : ""}`}
                onClick={() => handleNavigate(item)}
                title={collapsed ? item.label : undefined}
                aria-current={isActive ? "page" : undefined}
              >
                <span className="fin-nav-icon">
                  <IconComponent size={18} />
                </span>
                {!collapsed && (
                  <span className="fin-nav-label font-medium">{item.label}</span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Collapse Toggle Footer */}
      <div className="fin-sidebar-footer">
        <button
          type="button"
          className="fin-collapse-toggle-btn"
          onClick={onToggleCollapse}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <ChevronRight size={16} />
          ) : (
            <>
              <ChevronLeft size={16} />
              <span className="text-xs ml-1.5">Collapse Menu</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
