import React, { useState, useEffect } from "react";
import toast, { Toaster } from "react-hot-toast";
import { CheckCircle2, AlertTriangle, RefreshCw, Server, Zap } from "lucide-react";
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import Dashboard from "./pages/Dashboard";
import WorkspaceDirectory from "./pages/WorkspaceDirectory";
import SessionDetails from "./pages/SessionDetails";
import CreateSession from "./pages/CreateSession";
import DocumentLibrary from "./pages/DocumentLibrary";
import ConversationalResearch from "./pages/ConversationalResearch";
import ResearchWorkspace from "./pages/ResearchWorkspace";
import ReportView from "./pages/ReportView";
import OrchestrationView from "./pages/OrchestrationView";
import StubPage from "./components/StubPage";
import UploadDocumentModal from "./components/UploadDocumentModal";
import CreateSessionModal from "./components/CreateSessionModal";
import { INITIAL_SESSIONS } from "./data/seedData";
import { INITIAL_DOCUMENTS, getStoredDocuments } from "./data/documentData";
import api from "./services/api";
import "./index.css";
import { useAuth } from "./context/AuthContext";
import Login from "./pages/Login";

function normalizePageName(page) {
  if (!page) return "Dashboard";
  const p = page.toLowerCase();
  if (p === "dashboard") return "Dashboard";
  if (p.includes("session") || p.includes("workspace") || p.includes("directory")) return "Sessions";
  if (p.includes("doc") || p.includes("upload") || p.includes("knowledge")) return "Documents";
  if (p.includes("research") || p.includes("query") || p.includes("chat")) return "Research";
  if (p.includes("analysis") || p.includes("extract") || p.includes("flag") || p.includes("compare")) return "Analysis";
  if (p.includes("report")) return "Reports";
  if (p.includes("setting") || p.includes("orchestrat") || p.includes("agent") || p.includes("system")) return "Settings";
  return "Dashboard";
}

function mapBackendSession(s) {
  return {
    id: s.session_id,
    title: s.title,
    description: s.description || "",
    company: s.metadata?.company || "",
    researchType: s.metadata?.researchType || "General Research",
    objective: s.metadata?.objective || s.description || "",
    companyIds: [],
    status: s.status || "ACTIVE",
    createdAt: s.created_at
      ? new Date(s.created_at).toLocaleDateString()
      : null,
    documents: (s.document_ids || []).map((id) => ({
      id,
      name: id
    }))
  };
}

export default function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#0f172a",
        color: "#ffffff"
      }}>
        Checking authentication...
      </div>
    );
  }

  if (!user) {
    return <Login />;
  }

  return <AuthenticatedApp key={user.id} user={user} />;
}

function AuthenticatedApp({ user }) {

  async function refreshDocuments() {
    try {
      const liveDocs = await api.listDocuments();

      saveDocuments(liveDocs);

      const workspace = await api.getDefaultWorkspace();

      const liveSessions = await api.listWorkspaceSessions(
        workspace.workspace_id
      );

      const mapped = liveSessions.map(mapBackendSession);

      saveSessions(mapped);

      setActiveSession((previous) =>
        mapped.find((s) => s.id === previous?.id)
        || mapped[0]
        || null
      );

      return liveDocs;

    } catch (err) {
      saveDocuments([]);
      console.error("Refresh failed:", err);
      toast.error("Unable to refresh research data");
      return [];
    }
  }
  const [theme, setTheme] = useState(
    () => localStorage.getItem("finresearch_theme") || "dark"
  );
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [isSessionMutating, setIsSessionMutating] = useState(false);
  // Active top-level page
  const [activePage, setActivePage] = useState(() => {
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const qPage = urlParams.get("page");
      if (qPage) return normalizePageName(qPage);
      const stored = localStorage.getItem("finresearch_active_page");
      if (stored) return normalizePageName(stored);
    } catch {}
    return "Dashboard";
  });

  // Subview states for multi-view pages
  const [sessionSubView, setSessionSubView] = useState("directory"); // "directory" | "details" | "create"
  const [documentSubView, setDocumentSubView] = useState("library"); // "library" | "upload" | "details"
  const [analysisTab, setAnalysisTab] = useState("extraction"); // "extraction" | "redflags" | "overview" | "ingestion"

  function toggleTheme() {
    setTheme((currentTheme) => {
      const nextTheme = currentTheme === "dark" ? "light" : "dark";
      localStorage.setItem("finresearch_theme", nextTheme);
      return nextTheme;
    });
  }

  function toggleSidebar() {
    setSidebarCollapsed((prev) => !prev);
  }

const [workspaceId, setWorkspaceId] = useState(null);
const [sessions, setSessions] = useState([]);
const [activeSession, setActiveSession] = useState(null);
const [documents, setDocuments] = useState([]);

function saveDocuments(newDocs) {
  setDocuments(Array.isArray(newDocs) ? newDocs : []);
}

function saveSessions(updatedSessions) {
  setSessions(
    Array.isArray(updatedSessions) ? updatedSessions : []
  );
}
  // Backend Connectivity & Auto-detection
  const [backendStatus, setBackendStatus] = useState("checking"); // "live" | "mock" | "checking"
  const [backendInfo, setBackendInfo] = useState(null);
  const [isCheckingBackend, setIsCheckingBackend] = useState(false);

  async function checkBackend(silent = false) {
    setIsCheckingBackend(true);
    try {
      const health = await api.getHealth();
      if (health.online) {
        setBackendStatus(health.healthy ? "live" : "degraded");
        setBackendInfo(health);
        if (!silent) {
          if (health.healthy) {
            toast.success("Live AI Backend Connected (FastAPI on port 8000)", {
              id: "backend-status",
              duration: 4000,
              style: {
                background: "#091e17",
                color: "#34d399",
                border: "1px solid #059669",
                fontSize: "12px",
                fontWeight: "600",
              },
              iconTheme: {
                primary: "#34d399",
                secondary: "#091e17",
              },
            });
          } else {
            toast("Backend connected with degraded services", {
              id: "backend-status",
              icon: "⚠️",
              duration: 4500,
              style: {
                background: "#1c1408",
                color: "#fbbf24",
                border: "1px solid #d97706",
                fontSize: "12px",
                fontWeight: "600",
              },
            });
          }
        }
        // Load actual live documents from backend (authoritative backend data overrides local cache)
        
        await refreshDocuments();        

        // Load actual live sessions from backend
        try {
          const workspace = await api.getDefaultWorkspace();

          setWorkspaceId(workspace.workspace_id);

          const liveSessions = await api.listWorkspaceSessions(
            workspace.workspace_id
          );

          const mapped = liveSessions.map(mapBackendSession);

          saveSessions(mapped);

          setActiveSession((previous) =>
            mapped.find((s) => s.id === previous?.id)
            || mapped[0]
            || null
          );

        } catch (e) {
          setWorkspaceId(null);
          saveSessions([]);
          setActiveSession(null);

          console.error("Could not load research sessions:", e);
          toast.error("Unable to load your research sessions");
        }
      } else {
        setBackendStatus("offline");
        if (!silent) {
          toast.error("Backend offline — Cannot reach FastAPI server on port 8000", {
            id: "backend-status",
            duration: 4500,
            style: {
              background: "#1c0d0d",
              color: "#f87171",
              border: "1px solid #dc2626",
              fontSize: "12px",
              fontWeight: "600",
            },
          });
        }
      }
    } catch {
      setBackendStatus("offline");
      if (!silent) {
        toast.error("Backend offline — Cannot reach FastAPI server on port 8000", {
          id: "backend-status",
          duration: 4500,
          style: {
            background: "#1c0d0d",
            color: "#f87171",
            border: "1px solid #dc2626",
            fontSize: "12px",
            fontWeight: "600",
          },
        });
      }
    } finally {
      setIsCheckingBackend(false);
    }
  }

  useEffect(() => {
    checkBackend();
  }, [user.id]);



  useEffect(() => {
    function handlePopState() {
      try {
        const urlParams = new URLSearchParams(window.location.search);
        const qPage = urlParams.get("page");
        if (qPage) {
          setActivePage(normalizePageName(qPage));
        }
      } catch {}
    }
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  function navigateTo(target, subview = null, tab = null) {
    if (!target) return;

    let targetPage = "Dashboard";

    if (target === "dashboard" || target === "Dashboard") {
      targetPage = "Dashboard";
      setActivePage("Dashboard");
    } else if (target === "workspaces" || target === "Workspace Management") {
      targetPage = "Sessions";
      setActivePage("Sessions");
      setSessionSubView("directory");
    } else if (target === "sessions" || target === "Research Sessions") {
      targetPage = "Sessions";
      setActivePage("Sessions");
      setSessionSubView(subview || (activeSession ? "details" : "directory"));
    } else if (target === "documents" || target === "Document Library & Upload") {
      targetPage = "Documents";
      setActivePage("Documents");
      setDocumentSubView(subview || "library");
    } else if (target === "document_processing" || target === "Document Processing") {
      targetPage = "Documents";
      setActivePage("Documents");
      setDocumentSubView("details");
    } else if (target === "semantic_search" || target === "Semantic Search & Indexing") {
      targetPage = "Analysis";
      setActivePage("Analysis");
      setAnalysisTab("ingestion");
    } else if (target === "extraction" || target === "extraction_agent" || target === "Financial Extraction Agent") {
      targetPage = "Analysis";
      setActivePage("Analysis");
      setAnalysisTab("extraction");
    } else if (target === "evidence" || target === "evidence_validation" || target === "Evidence Validation") {
      targetPage = "Analysis";
      setActivePage("Analysis");
      setAnalysisTab("evidence");
    } else if (target === "redflags" || target === "red_flag_agent" || target === "Red Flag Analysis Agent") {
      targetPage = "Analysis";
      setActivePage("Analysis");
      setAnalysisTab("redflags");
    } else if (target === "analysis_results" || target === "Analysis Results") {
      targetPage = "Analysis";
      setActivePage("Analysis");
      setAnalysisTab("overview");
    } else if (target === "comparison_agent" || target === "Comparison Agent") {
      targetPage = "Research";
      setActivePage("Research");
    } else if (target === "research_agent" || target === "Research Agent") {
      targetPage = "Research";
      setActivePage("Research");
    } else if (target === "report_agent" || target === "Report Agent") {
      targetPage = "Reports";
      setActivePage("Reports");
    } else if (target === "pdf_export" || target === "PDF Export") {
      targetPage = "Reports";
      setActivePage("Reports");
    } else if (target === "settings" || target === "Settings") {
      targetPage = "Settings";
      setActivePage("Settings");
    } else {
      targetPage = normalizePageName(target);
      setActivePage(targetPage);

      // Track subviews
      if (target === "Create Session" || subview === "create") {
        setSessionSubView("create");
      } else if (target === "Session Details" || subview === "details") {
        setSessionSubView("details");
      } else if (targetPage === "Sessions") {
        if (subview) setSessionSubView(subview);
        else setSessionSubView("directory");
      }

      if (target === "Upload Document" || subview === "upload") {
        setDocumentSubView("upload");
      } else if (targetPage === "Documents") {
        if (subview) setDocumentSubView(subview);
        else setDocumentSubView("library");
      }

      if (tab) {
        setAnalysisTab(tab);
      }
    }

    try {
      localStorage.setItem("finresearch_active_page", targetPage);
      const url = new URL(window.location.href);
      url.searchParams.set("page", targetPage);
      window.history.replaceState({}, "", url.toString());
    } catch {}
  }

  // Session CRUD Handlers
  async function handleCreateSession(newSession) {
    try {
      const workspace = await api.getDefaultWorkspace();

      setWorkspaceId(workspace.workspace_id);

      const created = await api.createSession(
        workspace.workspace_id,
        {
          title: newSession.title,
          metadata: {
            company: newSession.company || "",
            researchType: newSession.researchType || "",
            objective: newSession.objective || ""
          },
          description:
            newSession.description ||
            newSession.objective ||
            ""
        }
      );



      const sessionWithId = {
        ...newSession,
        ...mapBackendSession(created)
      };

      setSessions((previous) => [
        sessionWithId,
        ...previous
      ]);

      setActiveSession(sessionWithId);
      setSessionSubView("details");

      toast.success(
        `Session "${sessionWithId.title}" created successfully!`
      );

      return sessionWithId;

    } catch (err) {
      console.error("Session creation failed:", err);
      toast.error("Unable to create research session");
      return null;
    }
  }

  // function handleUpdateSession(updatedSession) {
  //   const updated = sessions.map((s) => (s.id === updatedSession.id ? updatedSession : s));
  //   saveSessions(updated);
  //   if (activeSession?.id === updatedSession.id) {
  //     setActiveSession(updatedSession);
  //   }
  // }

  async function handleDuplicateSession(sessionToDup) {
    if (isSessionMutating) return;

    setIsSessionMutating(true);

    try {
      const result = await api.duplicateSession(
        sessionToDup.id
      );

      const duplicated = mapBackendSession(result);

      saveSessions([duplicated, ...sessions]);

      setActiveSession(duplicated);
      setSessionSubView("details");

      toast.success("Research session duplicated.");

    } catch (err) {
      toast.error(`Duplication failed: ${err.message}`);
    } finally {
      setIsSessionMutating(false);
    }
  }

  // function handleDeleteSession(sessionId) {
  //   const updated = sessions.filter((s) => s.id !== sessionId);
  //   saveSessions(updated);
  //   if (activeSession?.id === sessionId) {
  //     setActiveSession(updated[0] || null);
  //   }
  //   setSessionSubView("directory");
  //   toast.success("Research session removed.");
  // }

  async function handleUpdateSession(updatedSession) {
    if (isSessionMutating) return;

    setIsSessionMutating(true);

    try {
      const result = await api.updateSession(
        updatedSession.id,
        {
          title: updatedSession.title,
          metadata: {
            company: updatedSession.company || "",
            researchType: updatedSession.researchType || "",
            objective: updatedSession.objective || ""
          },
          description: updatedSession.description || ""
        }
      );

      const mapped = {
        ...updatedSession,
        ...mapBackendSession(result)
      };

      const updated = sessions.map(
        s => s.id === mapped.id ? mapped : s
      );

      saveSessions(updated);

      if (activeSession?.id === mapped.id) {
        setActiveSession(mapped);
      }

      toast.success("Research session updated.");

    } catch (err) {
      toast.error(`Session update failed: ${err.message}`);
    } finally {
      setIsSessionMutating(false);
    }
  }

  async function handleDeleteSession(sessionId) {
    if (isSessionMutating) return;

    setIsSessionMutating(true);

    try {
      await api.deleteSession(sessionId);

      const updated = sessions.filter(
        s => s.id !== sessionId
      );

      saveSessions(updated);

      if (activeSession?.id === sessionId) {
        setActiveSession(updated[0] || null);
      }

      setSessionSubView("directory");

      toast.success("Research session deleted.");

      await refreshDocuments();

    } catch (err) {
      toast.error(`Session deletion failed: ${err.message}`);
    } finally {
      setIsSessionMutating(false);
    }
  }

  return (
    <div className={`app-layout ${sidebarCollapsed ? "sidebar-is-collapsed" : ""}`} data-theme={theme}>
      {/* Clean, Professional Sidebar */}
      <Sidebar
        activePage={activePage}
        sessionSubView={sessionSubView}
        documentSubView={documentSubView}
        analysisTab={analysisTab}
        setPage={navigateTo}
        collapsed={sidebarCollapsed}
        onToggleCollapse={toggleSidebar}
      />

      <main className="main-content">
        {/* Clean, Disciplined Top Header */}
        <Header
          theme={theme}
          toggleTheme={toggleTheme}
          activePage={activePage}
          sessions={sessions}
          activeSession={activeSession}
          setActiveSession={setActiveSession}
          setPage={navigateTo}
          onToggleMobileSidebar={toggleSidebar}
        />

        <div className="page-container">
          {/* Module 1: Dashboard */}
          {activePage === "Dashboard" && (
            <Dashboard
              sessions={sessions}
              documents={documents}
              setPage={navigateTo}
              setActiveSession={setActiveSession}
              onDeleteSession={handleDeleteSession}
              onOpenUploadModal={() => setUploadModalOpen(true)}
              onOpenCreateModal={() => setCreateModalOpen(true)}
            />
          )}

          {/* Module 2: Research Sessions (Directory, Details, Create) */}
          {activePage === "Sessions" && (
            <>
              {sessionSubView === "create" ? (
                <CreateSession
                  onCreateSession={handleCreateSession}
                  onCancel={() => setSessionSubView("directory")}
                />
              ) : sessionSubView === "details" && activeSession ? (
                <SessionDetails
                  session={activeSession}
                  onBack={() => setSessionSubView("directory")}
                  onUpdateSession={handleUpdateSession}
                  onDuplicateSession={handleDuplicateSession}
                  onDeleteSession={handleDeleteSession}
                  onLaunchInteractive={() => navigateTo("Research")}
                  onNavigateToReports={() => navigateTo("Reports")}
                  onNavigateToDocs={() => navigateTo("Documents")}
                />
              ) : (
                <WorkspaceDirectory
                  sessions={sessions}
                  activeSession={activeSession}
                  onSelectSession={(s) => {
                    setActiveSession(s);
                    setSessionSubView("details");
                  }}
                  onViewSessionDetails={(s) => {
                    setActiveSession(s);
                    setSessionSubView("details");
                  }}
                  onLaunchInteractive={(s) => {
                    setActiveSession(s);
                    navigateTo("Research");
                  }}
                  onOpenCreateModal={() => setCreateModalOpen(true)}
                  onDuplicateSession={handleDuplicateSession}
                  onDeleteSession={handleDeleteSession}
                />
              )}
            </>
          )}

          {/* Module 3: Financial Documents (Library, Upload, Search) */}
          {activePage === "Documents" && (
            <DocumentLibrary
              documents={documents}
              onUpdateDocuments={refreshDocuments}
              sessions={sessions}
              activeSession={activeSession}
              setActiveSession={setActiveSession}
              setPage={navigateTo}
              initialSubView={documentSubView}
              onOpenDocumentSession={(companyKey) => {
                const s = sessions.find((ses) => ses.companyIds?.includes(companyKey));
                if (s) {
                  setActiveSession(s);
                }
                navigateTo("Research");
              }}
            />
          )}

          {/* Module 4: AI Research (Milestone 3 — Conversational Research Agent) */}
          {activePage === "Research" && (
            <ConversationalResearch
              documents={documents}
              session={activeSession}
              sessions={sessions}
              setActiveSession={setActiveSession}
              setPage={navigateTo}
            />
          )}

          {/* Module 5: Financial Analysis (Extraction, Red Flags, Peer Comparison) */}
          {activePage === "Analysis" && (
            <ResearchWorkspace
              documents={documents}
              session={activeSession}
              sessions={sessions}
              setActiveSession={setActiveSession}
              setPage={navigateTo}
              initialMode="interactive"
              activeTabOverride={analysisTab}
              onUpdateSession={handleUpdateSession}
              onDuplicateSession={handleDuplicateSession}
              onDeleteSession={handleDeleteSession}
              onOpenCreateModal={() => setCreateModalOpen(true)}
            />
          )}

          {/* Module 6: Executive Reports (Milestone 4 — Under Development Stub) */}
          {activePage === "Reports" && (
            <StubPage
              milestone="Milestone 4"
              title="Executive Report Generation Agent"
              agentName="Executive Report Agent"
              description="Automated report compilation, cross-agent synthesis, and exportable PDF dossiers are scheduled for delivery in Milestone 4."
              plannedFeatures={[
                {
                  title: "Automated PDF Dossier Assembly",
                  description: "Compiles verified financials, forensic flags, and chart graphics into a downloadable institutional report."
                },
                {
                  title: "Multi-Agent Synthesis & Executive Summaries",
                  description: "Condenses insights from the Document, Extraction, and Red Flag agents into a board-ready executive memo."
                },
                {
                  title: "Auditor Verification Footnotes",
                  description: "Embeds clickable provenance references and page citations directly into the exported document."
                },
                {
                  title: "Customizable Report Templates",
                  description: "Supports equity research, credit risk, and forensic audit dossier configurations."
                }
              ]}
              setPage={navigateTo}
            />
          )}

          {/* Module 7: Multi-Agent System & Orchestration Diagnostics */}
          {activePage === "Settings" && (
            <OrchestrationView
              sessions={sessions}
              activeSession={activeSession}
              setActiveSession={setActiveSession}
              setPage={navigateTo}
            />
          )}
        </div>
      </main>

      {/* Lightweight Upload Filing Modal */}
      <UploadDocumentModal
        open={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        onUploadSuccess={refreshDocuments}
      />

      {/* Lightweight Create Session Modal */}
      <CreateSessionModal
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onCreateSession={(newSession) => {
          handleCreateSession(newSession);
          setCreateModalOpen(false);
        }}
      />

      {/* React Hot Toast Notifications Container */}
      <Toaster
        position="top-right"
        reverseOrder={false}
        toastOptions={{
          style: {
            background: "#0f172a",
            color: "#f8fafc",
            border: "1px solid #334155",
            fontSize: "12px",
            boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.4)",
          },
        }}
      />
    </div>
  );
}
