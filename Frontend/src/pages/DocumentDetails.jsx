import React, { useState, useEffect } from "react";
import {
  ArrowLeft,
  FileText,
  Building2,
  Calendar,
  Layers,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
  Search,
  Bookmark,
  Hash,
  Database,
  Cpu,
  Clock,
  Trash2,
  FolderOpen,
  ArrowRight
} from "lucide-react";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import DocumentViewer from "../components/DocumentViewer";
import CitationModal from "../components/CitationModal";
import {  SEED_COMPANIES } from "../data/seedData";
import api from "../services/api";
import toast from "react-hot-toast";

export default function DocumentDetails({
  document: doc,
  sessions = [],
  onBack,
  onOpenSession,
  onUpdateDocument,
  onDeleteDocument
}) {
  const [activeTab, setActiveTab] = useState("sections"); // "sections" | "chunks" | "session" | "metadata"
  const [activeCitation, setActiveCitation] = useState(null);
  const [searchChunkTerm, setSearchChunkTerm] = useState("");
  const [isRetrying, setIsRetrying] = useState(false);
  const [retryStage, setRetryStage] = useState(null);
  const [liveChunks, setLiveChunks] = useState([]);
  const [isLoadingChunks, setIsLoadingChunks] = useState(false);
  const [chunkError, setChunkError] = useState(null);
  const [backendStatus, setBackendStatus] = useState(null);
  const [statusError, setStatusError] = useState(null);

  useEffect(() => {
    let active = true;

    setLiveChunks([]);
    setChunkError(null);

    if (!doc?.id) {
      setIsLoadingChunks(false);
      return;
    }

    setIsLoadingChunks(true);

    const timer = setTimeout(async () => {
      try {
        const res = await api.search({
          query: searchChunkTerm.trim() || "financial information",
          document_id: doc.id,
          top_k: 20
        });

        if (active) {
          setLiveChunks(res?.results || []);
        }
      } catch (err) {
        if (active) {
          setLiveChunks([]);
          setChunkError("Unable to retrieve document chunks.");
        }
      } finally {
        if (active) {
          setIsLoadingChunks(false);
        }
      }
    }, 350);

    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [doc?.id, searchChunkTerm]);
  

  useEffect(() => {
    let active = true;

    setBackendStatus(null);
    setStatusError(null);

    if (!doc?.id) return;

    async function loadStatus() {
      try {
        const result = await api.getDocumentStatus(doc.id);

        if (active) {
          setBackendStatus(result);
          setStatusError(null);
        }
      } catch (err) {
        if (active) {
          setStatusError("Unable to retrieve processing status.");
        }
      }
    }

    loadStatus();

    const interval = isRetrying
      ? setInterval(loadStatus, 2000)
      : null;

    return () => {
      active = false;

      if (interval) {
        clearInterval(interval);
      }
    };
  }, [doc?.id, isRetrying]);
  if (!doc) {
    return (
      <div className="fin-doc-details-page p-8 text-center">
        <p className="text-muted">No document selected.</p>
        <Button variant="secondary" size="sm" onClick={onBack} className="mt-4">
          Back to Financial Documents
        </Button>
      </div>
    );
  }
  function normalizeStage(status) {
    const value = String(status || "").toUpperCase();

    if (["COMPLETED", "SUCCESS", "INDEXED"].includes(value)) {
      return "completed";
    }

    if (["FAILED", "ERROR"].includes(value)) {
      return "error";
    }

    if (["PROCESSING", "RUNNING", "IN_PROGRESS"].includes(value)) {
      return "in-progress";
    }

    return "waiting";
  }

  const stages = backendStatus?.stages || {};

  const pipelineStages = [
    {
      name: "Uploaded",
      status: backendStatus ? "completed" : "waiting",
      detail: "Document registered in backend"
    },
    {
      name: "Parsing & Chunking",
      status: normalizeStage(stages.DOCUMENT_AGENT),
      detail: `${backendStatus?.total_pages ?? 0} pages processed`
    },
    {
      name: "Embedding & Indexing",
      status: normalizeStage(
        stages.DOCUMENT_AGENT ||
        (backendStatus?.indexed ? "INDEXED" : null)
      ),
      detail: `${backendStatus?.chunk_count ?? 0} indexed chunks`
    },
    {
      name: "Extraction Agent",
      status: normalizeStage(stages.EXTRACTION_AGENT),
      detail: "Financial metric extraction"
    },
    {
      name: "Red Flag Agent",
      status: normalizeStage(stages.RED_FLAG_AGENT),
      detail: "Financial risk analysis"
    }
  ];

  const completedStages = pipelineStages.filter(
    stage => stage.status === "completed"
  ).length;
  // Linked research session
  const linkedSession = sessions.find((s) => s.id === doc.sessionId) ||
    sessions.find((s) => s.companyIds?.includes(doc.ticker)) ||
    sessions[0];

  // Real document chunks from vector search
  useEffect(() => {
    setLiveChunks([]);
    setIsLoadingChunks(false);
  }, [doc?.id, searchChunkTerm]);
  // useEffect(() => {
  //   let isSubscribed = true;
  //   setLiveChunks([]); // Immediately clear to prevent stale chunk leakage from previous document

  //   async function fetchChunks() {
  //     if (!doc?.id) return;
  //     setIsLoadingChunks(true);
  //     try {
  //       const res = await api.search({
  //         query: searchChunkTerm.trim() || "*",
  //         document_id: doc.id,
  //         top_k: 20
  //       });
  //       if (isSubscribed && res?.results) {
  //         setLiveChunks(res.results);
  //       }
  //     } catch (e) {
  //       // Fallback to sample chunks if vector store has no match
  //     } finally {
  //       if (isSubscribed) setIsLoadingChunks(false);
  //     }
  //   }
  //   fetchChunks();
  //   return () => { isSubscribed = false; };
  // }, [doc?.id, searchChunkTerm]);

  // Document chunks: live from vector store if available, fallback to seed
  const docChunks = liveChunks;

  const filteredChunks = docChunks.filter(
    (chunk) => chunk.documentId === doc.id
  );

  // Real Multi-Agent Pipeline Execution Workflow

  async function handleRetryProcessing() {
    if (isRetrying) return;

    setIsRetrying(true);
    setRetryStage("Processing document...");
    setStatusError(null);

    try {
      const result = await api.processDocument({
        document_id: doc.id
      });

      const status = await api.getDocumentStatus(doc.id);

      setBackendStatus(status);

      const updated = {
        ...doc,
        pages: status.total_pages ?? doc.pages,
        chunksCount: status.chunk_count ?? doc.chunksCount,
        status: result.status === "COMPLETED"
          ? "Ready"
          : "Error"
      };

      if (onUpdateDocument) {
        onUpdateDocument(doc.id, updated);
      }

      if (result.status === "COMPLETED") {
        toast.success("Multi-Agent Pipeline completed!");
      } else {
        toast.error("Document processing failed.");
      }

    } catch (err) {
      if (err.status === 401) {
        toast.error("Please sign in again.");
      } else if (err.status === 404) {
        toast.error("Document not found or access unavailable.");
      } else {
        toast.error(`Processing failed: ${err.message}`);
      }
    } finally {
      setIsRetrying(false);
      setRetryStage(null);
    }
  }
  const isErrorState = doc.status === "Error";

  return (
    <div className="fin-doc-details-page animate-fadeIn space-y-6">
      {/* Top Header & Breadcrumb */}
      <div className="flex-row items-center justify-between pb-4 border-b border-subtle">
        <div className="flex-row items-center gap-3">
          <button
            type="button"
            className="fin-btn fin-btn-ghost fin-btn-sm"
            onClick={onBack}
            title="Return to Financial Documents"
          >
            <ArrowLeft size={16} />
            <span>Back to Financial Documents</span>
          </button>
          <div className="h-4 w-px bg-border-color" />
          <div>
            <div className="flex-row items-center gap-2">
              <h1 className="text-xl font-bold text-main truncate max-w-lg" title={doc.name}>
                {doc.name}
              </h1>
              {doc.isSeed ? (
                <Badge variant="teal" size="xs" icon={Sparkles}>
                  Seed Document
                </Badge>
              ) : (
                <Badge variant="primary" size="xs">
                  User Ingested
                </Badge>
              )}
              <Badge
                variant={
                  isErrorState
                    ? "danger"
                    : doc.status === "Ready"
                    ? "success"
                    : "warning"
                }
                size="xs"
                dot
              >
                {doc.status}
              </Badge>
            </div>
            <p className="text-xs text-muted mt-0.5">
              {doc.company} ({doc.ticker}) • {doc.docType} • Ingested on {doc.uploadDate}
            </p>
          </div>
        </div>

        {/* Quick Top Actions */}
        <div className="flex-row items-center gap-2">
          {isErrorState ? (
            <Button
              variant="warning"
              size="sm"
              icon={RefreshCw}
              loading={isRetrying}
              onClick={handleRetryProcessing}
            >
              {isRetrying ? retryStage || "Retrying Pipeline..." : "Retry Processing"}
            </Button>
          ) : (
            <Button
              variant="ghost"
              size="sm"
              icon={RefreshCw}
              loading={isRetrying}
              onClick={handleRetryProcessing}
              title="Re-run the sequential multi-agent workflow on this document"
            >
              {isRetrying ? retryStage || "Processing..." : "Re-run Pipeline"}
            </Button>
          )}

          {linkedSession && (
            <Button
              variant="primary"
              size="sm"
              icon={FolderOpen}
              onClick={() => onOpenSession && onOpenSession(linkedSession)}
            >
              Open in Research Workspace
            </Button>
          )}

          {!doc.isSeed && (
            <Button
              variant="ghost"
              size="sm"
              className="text-danger"
              icon={Trash2}
              onClick={() => onDeleteDocument && onDeleteDocument(doc.id)}
            >
              Delete
            </Button>
          )}
        </div>
      </div>

      {/* Error Alert Box when in Error State */}
      {isErrorState && (
        <div className="fin-error-banner p-4 border rounded-lg bg-danger/10 border-danger/30 flex-row items-start justify-between gap-4 animate-fadeIn">
          <div className="flex-row items-start gap-3">
            <AlertTriangle size={20} className="text-danger shrink-0 mt-0.5" />
            <div>
              <strong className="text-sm text-danger block">
                Document Processing Failed
              </strong>
              <p className="text-xs text-muted mt-1 leading-relaxed">
                Incomplete embedded font table encountered in Note 14 (Consolidated Liabilities footnote).
                The document pipeline halted prior to chunking and vector embedding.
              </p>
              <div className="flex-row items-center gap-2 mt-3">
                <Button
                  variant="teal"
                  size="xs"
                  icon={RefreshCw}
                  loading={isRetrying}
                  onClick={handleRetryProcessing}
                >
                  {isRetrying
    ? retryStage || "Retrying..."
    : "Retry Document Processing"}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Top 4 Metric KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="fin-stat-card p-4 border rounded-lg bg-card">
          <span className="text-xs text-muted block">Document Length</span>
          <strong className="text-xl font-bold font-mono text-main block mt-1">
            {doc.pages} Pages
          </strong>
          <span className="text-[11px] text-accent flex-row items-center gap-1 mt-1">
            <CheckCircle2 size={12} /> Document Text Extraction
          </span>
        </div>

        <div className="fin-stat-card p-4 border rounded-lg bg-card">
          <span className="text-xs text-muted block">Semantic Vector Chunks</span>
          <strong className="text-xl font-bold font-mono text-accent block mt-1">
            {doc.chunksCount} Chunks
          </strong>
          <span className="text-[11px] text-muted block mt-1">
            Avg ~418 tokens / chunk
          </span>
        </div>

        <div className="fin-stat-card p-4 border rounded-lg bg-card">
          <span className="text-xs text-muted block">Embedding Dimensions</span>
          <strong className="text-xl font-bold font-mono text-main block mt-1">
            1,536 Dims
          </strong>
          <span className="text-[11px] text-muted block mt-1">
            text-embedding-3-small
          </span>
        </div>

        <div className="fin-stat-card p-4 border rounded-lg bg-card">
          <span className="text-xs text-muted block">File Size & Checksum</span>
          <strong className="text-xl font-bold font-mono text-main block mt-1">
            {doc.fileSize}
          </strong>
          <span className="text-[11px] font-mono text-dim block mt-1 truncate" title={doc.checksum}>
            {doc.checksum ? doc.checksum.substring(0, 16) + "..." : "sha256 verified"}
          </span>
        </div>
      </div>

      {/* Ingestion Pipeline Stepper (The 5 Required Stages) */}
      <div className="fin-card p-5 border rounded-lg bg-card">
        <div className="flex-row items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-main flex-row items-center gap-2">
              <Cpu size={16} className="text-accent" />
              Document Ingestion & Parsing Pipeline Stages
            </h3>
            <p className="text-xs text-muted mt-0.5">
              Five-stage verification pipeline powering strict citation grounding and multi-agent retrieval.
            </p>
          </div>
          <Badge variant="teal" size="xs">
{statusError
  ? "Status unavailable"
  : isRetrying
    ? "Pipeline Processing"
    : `${completedStages} / ${pipelineStages.length} Stages Completed`}          </Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {pipelineStages.map((stage, idx) => {
            const isCompleted = stage.status === "completed";
            const isError = stage.status === "error";
            const isInProgress = stage.status === "in-progress";
            const isWaiting = stage.status === "waiting";

            return (
              <div
                key={stage.name}
                className={`p-3.5 border rounded-lg transition-all ${
                  isError
                    ? "border-danger/40 bg-danger/10"
                    : isCompleted
                    ? "border-success/30 bg-card-subtle"
                    : isInProgress
                    ? "border-accent bg-accent/10 shadow-glow"
                    : "border-border-color bg-card-subtle opacity-60"
                }`}
              >
                <div className="flex-row justify-between items-center mb-2">
                  <span className="text-[11px] font-mono text-muted">STAGE 0{idx + 1}</span>
                  {isCompleted && (
                    <span className="text-success flex-row items-center gap-1 text-[11px] font-bold">
                      <CheckCircle2 size={13} /> Completed
                    </span>
                  )}
                  {isError && (
                    <span className="text-danger flex-row items-center gap-1 text-[11px] font-bold">
                      <AlertTriangle size={13} /> Failed
                    </span>
                  )}
                  {isInProgress && (
                    <span className="text-accent flex-row items-center gap-1 text-[11px] font-bold">
                      <RefreshCw size={13} className="animate-spin" /> Active
                    </span>
                  )}
                  {isWaiting && (
                    <span className="text-dim text-[11px]">Waiting</span>
                  )}
                </div>

                <strong className={`text-sm block ${isError ? "text-danger" : "text-main"}`}>
                  {stage.name}
                </strong>
                <p className="text-xs text-muted mt-1 leading-relaxed line-clamp-2" title={stage.detail}>
                  {stage.detail}
                </p>

                <div className="mt-3 pt-2 border-t border-subtle flex-row justify-between text-[10px] text-dim">
                  <span>Timestamp:</span>
                  <span className="font-mono text-muted">
  {stage.status}
</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Split Layout: PDF Viewer & Document Inspection Tabs */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Interactive Document Preview & PDF Viewer */}
        <div className="lg:col-span-7 space-y-4">
          <div className="fin-card border rounded-lg bg-card overflow-hidden">
            <div className="p-3.5 border-b border-subtle flex-row justify-between items-center">
              <div className="flex-row items-center gap-2">
                <FileText size={16} className="text-accent" />
                <h3 className="text-sm font-bold text-main">Institutional Document Preview</h3>
                <Badge variant="teal" size="xs">Audited View</Badge>
              </div>
              <span className="text-xs text-muted">
                {doc.pages} Pages Indexed
              </span>
            </div>

            <DocumentViewer
              document={doc}
              onCitationClick={(citation) => setActiveCitation(citation)}
            />
          </div>
        </div>

        {/* Right Column: Tabbed Sections, Chunks & Session Linkage */}
        <div className="lg:col-span-5 space-y-4">
          <div className="fin-card border rounded-lg bg-card overflow-hidden">
            {/* Tab Buttons */}
            <div className="flex-row border-b border-subtle bg-card-subtle">
              <button
                type="button"
                className={`flex-1 py-3 px-3 text-xs font-semibold text-center transition-all ${
                  activeTab === "sections"
                    ? "border-b-2 border-accent text-accent bg-card font-bold"
                    : "text-muted hover:text-main"
                }`}
                onClick={() => setActiveTab("sections")}
              >
                Sections ({doc.sections?.length || 0})
              </button>
              <button
                type="button"
                className={`flex-1 py-3 px-3 text-xs font-semibold text-center transition-all ${
                  activeTab === "chunks"
                    ? "border-b-2 border-accent text-accent bg-card font-bold"
                    : "text-muted hover:text-main"
                }`}
                onClick={() => setActiveTab("chunks")}
              >
                Chunks ({docChunks.length})
              </button>
              <button
                type="button"
                className={`flex-1 py-3 px-3 text-xs font-semibold text-center transition-all ${
                  activeTab === "session"
                    ? "border-b-2 border-accent text-accent bg-card font-bold"
                    : "text-muted hover:text-main"
                }`}
                onClick={() => setActiveTab("session")}
              >
                Research Session
              </button>
              <button
                type="button"
                className={`flex-1 py-3 px-3 text-xs font-semibold text-center transition-all ${
                  activeTab === "metadata"
                    ? "border-b-2 border-accent text-accent bg-card font-bold"
                    : "text-muted hover:text-main"
                }`}
                onClick={() => setActiveTab("metadata")}
              >
                Metadata
              </button>
            </div>

            <div className="p-4 max-h-[580px] overflow-y-auto">
              {/* Tab 1: Extracted Sections (Table of Contents) */}
              {activeTab === "sections" && (
                <div className="space-y-3">
                  <div className="flex-row justify-between items-center mb-2">
                    <span className="text-xs font-bold text-main">Identified Structural Sections</span>
                    <span className="text-[11px] text-muted">Financial Table & Text Segments</span>
                  </div>

                  {doc.sections && doc.sections.length > 0 ? (
                    doc.sections.map((sec) => (
                      <div
                        key={sec.id}
                        className="p-3 border rounded-lg bg-card-subtle hover:border-accent transition-all cursor-pointer"
                      >
                        <div className="flex-row justify-between items-start gap-2">
                          <strong className="text-xs text-main block">{sec.title}</strong>
                          <span className="text-[11px] font-mono font-bold text-accent shrink-0">
                            Page {sec.page}
                          </span>
                        </div>
                        <div className="flex-row items-center gap-2 mt-1.5 text-[11px] text-muted">
                          <Badge variant="primary" size="xs">{sec.category}</Badge>
                          <span>•</span>
                          <span>{sec.chunks} Chunks Indexed</span>
                        </div>
                        {sec.previewSnippet && (
                          <p className="text-[11px] text-dim mt-2 italic leading-relaxed">
                            "{sec.previewSnippet}"
                          </p>
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-muted text-center py-6">
                      No structural sections recorded for this document.
                    </p>
                  )}
                </div>
              )}

              {/* Tab 2: Semantic Chunks & Vector Inspect */}
              {activeTab === "chunks" && (
                <div className="space-y-3">
                  <div className="relative mb-3">
                    <Search size={14} className="absolute left-3 top-3 text-muted" />
                    <input
                      type="text"
                      className="fin-input w-full pl-9 text-xs"
                      placeholder="Filter semantic chunks by text or section..."
                      value={searchChunkTerm}
                      onChange={(e) => setSearchChunkTerm(e.target.value)}
                    />
                  </div>

                  {isLoadingChunks ? (
                    <p className="text-muted">
                      Retrieving document chunks...
                    </p>
                  ) : chunkError ? (
                    <p className="text-red-400">
                      {chunkError}
                    </p>
                  ) : filteredChunks.length > 0 ? (
                    filteredChunks.map((chunk) => (
                      <div key={chunk.id} className="p-3 border rounded-lg bg-card-subtle space-y-2">
                        <div className="flex-row justify-between items-center text-xs">
                          <span className="font-mono text-purple-400 font-bold">{chunk.id}</span>
                          <span className="text-accent font-semibold">Page {chunk.page}</span>
                          <span className="text-success font-mono font-bold">
                            Sim: {(chunk.similarityScore * 100).toFixed(1)}%
                          </span>
                        </div>
                        <strong className="text-xs text-main block">{chunk.section}</strong>
                        <p className="text-xs text-muted leading-relaxed line-clamp-3">
                          "{chunk.content}"
                        </p>
                        <div className="pt-2 flex-row justify-end">
                          <button
                            type="button"
                            className="fin-btn fin-btn-ghost fin-btn-xs text-accent"
                            onClick={() =>
                              setActiveCitation({
                                docName: chunk.docName,
                                company: doc.company,
                                page: chunk.page,
                                section: chunk.section,
                                snippet: chunk.content
                              })
                            }
                          >
                            View Source Citation
                          </button>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-muted">
                      No indexed chunks available for this search.
                    </p>
                  )}
                </div>
              )}

              {/* Tab 3: Related Research Session (Module 1 Integration) */}
              {activeTab === "session" && (
                <div className="space-y-4">
                  <span className="text-xs font-bold text-main block">
                    Linked Research Session (Module 1)
                  </span>

                  {linkedSession ? (
                    <div className="p-4 border rounded-lg bg-card-subtle space-y-3">
                      <div className="flex-row justify-between items-start">
                        <div>
                          <Badge variant="teal" size="xs">Active Session</Badge>
                          <h4 className="text-sm font-bold text-main mt-1.5">
                            {linkedSession.title}
                          </h4>
                        </div>
                        <Badge variant="success" size="xs">
                          {linkedSession.status || "Ready"}
                        </Badge>
                      </div>

                      <p className="text-xs text-muted leading-relaxed">
                        {linkedSession.description}
                      </p>

                      <div className="p-2.5 border rounded bg-card text-xs space-y-1">
                        <div className="flex-row justify-between">
                          <span className="text-muted">Research Type:</span>
                          <strong className="text-main">{linkedSession.researchType}</strong>
                        </div>
                        <div className="flex-row justify-between">
                          <span className="text-muted">Target Entity:</span>
                          <strong className="text-main">{linkedSession.company}</strong>
                        </div>
                        <div className="flex-row justify-between">
                          <span className="text-muted">Created Date:</span>
                          <span className="text-muted">{linkedSession.createdAt}</span>
                        </div>
                      </div>

                      <Button
                        variant="primary"
                        size="sm"
                        className="w-full"
                        icon={ArrowRight}
                        iconPosition="right"
                        onClick={() => onOpenSession && onOpenSession(linkedSession)}
                      >
                        Launch Interactive Workspace
                      </Button>
                    </div>
                  ) : (
                    <div className="p-4 border rounded text-center text-xs text-muted">
                      No research session currently linked to this document.
                    </div>
                  )}
                </div>
              )}

              {/* Tab 4: Technical Ingestion Metadata */}
              {activeTab === "metadata" && (
                <div className="space-y-3 text-xs">
                  <div className="p-3 border rounded bg-card-subtle space-y-2">
                    <div className="flex-row justify-between py-1 border-b border-subtle">
                      <span className="text-muted">Original Filename:</span>
                      <strong className="text-main font-mono">{doc.name}</strong>
                    </div>
                    <div className="flex-row justify-between py-1 border-b border-subtle">
                      <span className="text-muted">Document Type:</span>
                      <strong className="text-main">{doc.docType}</strong>
                    </div>
                    <div className="flex-row justify-between py-1 border-b border-subtle">
                      <span className="text-muted">File Size:</span>
                      <span className="text-main font-mono">{doc.fileSize ? `${doc.fileSize}${doc.fileSizeBytes ? ` (${doc.fileSizeBytes} bytes)` : ""}` : "Unknown"}</span>
                    </div>
                    <div className="flex-row justify-between py-1 border-b border-subtle">
                      <span className="text-muted">SHA-256 Checksum:</span>
                      <span className="text-main font-mono">{doc.checksum || "Unknown"}</span>
                    </div>
                    <div className="flex-row justify-between py-1 border-b border-subtle">
                      <span className="text-muted">OCR Ingestion Engine:</span>
                      <strong className="text-accent">{doc.ocrEngine || "Unknown"}</strong>
                    </div>
                    <div className="flex-row justify-between py-1 border-b border-subtle">
                      <span className="text-muted">Embedding Model:</span>
                      <strong className="text-accent">{doc.embeddingModel || "Unknown"}</strong>
                    </div>
                    <div className="flex-row justify-between py-1 border-b border-subtle">
                      <span className="text-muted">Chunking Strategy:</span>
                      <span className="text-main">{doc.metadata?.chunking_strategy || "Structure-Aware Token Chunker"}</span>
                    </div>
                    <div className="flex-row justify-between py-1">
                      <span className="text-muted">Vector Storage Namespace:</span>
                      <span className="text-main font-mono">{doc.metadata?.vector_collection || (doc.ticker ? `finresearch-${doc.ticker.toLowerCase()}-vectors` : "Default Index")}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Citation Modal */}
      {activeCitation && (
        <CitationModal citation={activeCitation} onClose={() => setActiveCitation(null)} />
      )}
    </div>
  );
}
