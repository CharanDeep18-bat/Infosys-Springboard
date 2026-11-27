// Multi-Agent Orchestration Layer Data Store for Module 4
import { SEED_COMPANIES } from "./seedData";

export const AGENT_ROLES = [
  {
    id: "documentAgent",
    name: "Document Agent",
    shortName: "Doc Agent",
    icon: "FileText",
    color: "#3b82f6", // Blue
    category: "Ingestion & Indexing",
    responsibility: "OCR text parsing, table coordinate extraction, footnote segmentation, and 1536-dimensional vector embedding generation.",
    defaultStatus: "Completed",
    currentTask: "Indexed 3,000 dense semantic vector chunks across INFY and TCS annual reports.",
    lastActivity: "2 mins ago",
    duration: "4.2s",
    stats: "3,000+ chunks • 804 pages",
    inputs: ["Audited PDF filings", "SEC Form 10-K", "Integrated Annual Reports"],
    outputs: ["HNSW vector index", "Normalized table grids", "Document text streams"],
    dependencies: ["Document Upload"],
    conditionalNote: "Always executed as Stage 1 for any ingested filing."
  },
  {
    id: "extractionAgent",
    name: "Extraction Agent",
    shortName: "Extract Agent",
    icon: "Layers",
    color: "#10b981", // Emerald
    category: "Financial Analytics",
    responsibility: "Harvester of GAAP/IFRS financial line items (Revenue, EBIT, Net Income, FCF, CapEx, Diluted EPS) and ratio reconciliation.",
    defaultStatus: "Completed",
    currentTask: "Harvested 14 core metrics and 7 financial ratios with coordinate anchors.",
    lastActivity: "1 min ago",
    duration: "2.8s",
    stats: "14 core metrics • 7 ratios",
    inputs: ["Indexed chunks from Document Agent", "Consolidated P&L & Balance Sheet schedules"],
    outputs: ["GAAP metrics matrix", "Profitability & liquidity ratios", "Reconciliation table"],
    dependencies: ["Document Agent"],
    conditionalNote: "Requires successful completion of Document Agent."
  },
  {
    id: "redFlagAgent",
    name: "Red Flag Agent",
    shortName: "Risk Agent",
    icon: "AlertTriangle",
    color: "#f59e0b", // Amber
    category: "Forensic Audit",
    responsibility: "Unprompted forensic anomaly detection: margin degradation, debt surges, customer/geographic concentration, and auditor qualifications.",
    defaultStatus: "Completed",
    currentTask: "Surfaced 5 forensic anomalies across IT discretionary spend freeze and headcount contraction.",
    lastActivity: "45s ago",
    duration: "3.1s",
    stats: "5 forensic anomalies • 8 heuristics",
    inputs: ["Extracted metrics", "Item 1A Risk Factors", "Footnote disclosures", "Auditor reports"],
    outputs: ["Forensic risk matrix", "Severity scorecards (High/Med/Low)", "Evidence snippets"],
    dependencies: ["Extraction Agent"],
    conditionalNote: "Can run independently as a standalone Forensic Scan."
  },
  {
    id: "comparisonAgent",
    name: "Comparison Agent",
    shortName: "Peer Agent",
    icon: "GitCompare",
    color: "#a855f7", // Purple
    category: "Peer Benchmarking",
    responsibility: "Cross-company benchmarking, EBIT margin variance spreads, deal TCV rankings, and competitive peer positioning.",
    defaultStatus: "Completed",
    currentTask: "Compiled 387 bps EBIT margin variance matrix for INFY vs TCS.",
    lastActivity: "30s ago",
    duration: "1.9s",
    stats: "387 bps EBIT spread • $42.7B vs $17.7B TCV",
    inputs: ["Multi-company metrics from Extraction Agent", "Segmental disclosures"],
    outputs: ["Side-by-side variance matrix", "Peer ranking scorecards", "Spread drivers"],
    dependencies: ["Extraction Agent", "Red Flag Agent"],
    conditionalNote: "CONDITIONAL BRANCH: Activated only for multi-company peer research sessions. Automatically bypassed for single-company runs."
  },
  {
    id: "researchAgent",
    name: "Research Agent",
    shortName: "Reasoning Agent",
    icon: "Bot",
    color: "#06b6d4", // Cyan
    category: "Conversational Reasoning",
    responsibility: "Multi-part financial reasoning engine decomposing complex analyst inquiries with step-by-step vector retrieval and strict citations.",
    defaultStatus: "Completed",
    currentTask: "Multi-step reasoning engine active for conversational queries with citation grounding.",
    lastActivity: "15s ago",
    duration: "Live",
    stats: "Sub-second retrieval • Strict citations",
    inputs: ["Analyst query", "Vector database", "Extracted ratios", "Red flag evidence"],
    outputs: ["Reasoning chains", "Synthesized analyst responses", "Grounded page citations"],
    dependencies: ["Extraction Agent", "Red Flag Agent", "Comparison Agent (if multi-company)"],
    conditionalNote: "Can be queried interactively at any time after Extraction completes."
  },
  {
    id: "reportAgent",
    name: "Report Agent",
    shortName: "Dossier Agent",
    icon: "Printer",
    color: "#ec4899", // Pink
    category: "Dossier Generation",
    responsibility: "Compiles outputs from all upstream agents into an institutional publication-grade analyst research report with exportable PDF formatting.",
    defaultStatus: "Completed",
    currentTask: "Compiled 5-part institutional research report ready for PDF export.",
    lastActivity: "Just now",
    duration: "1.4s",
    stats: "5 report sections • PDF export ready",
    inputs: ["Syntheses from all active agents", "Executive summaries", "Grounding citations"],
    outputs: ["Structured analyst report", "Print-ready stylesheet", "Dossier metadata"],
    dependencies: ["Research Agent", "Red Flag Agent", "Comparison Agent"],
    conditionalNote: "Final stage triggered when an analyst requests an exportable dossier."
  }
];

export const WORKFLOW_PRESETS = [];
export const INITIAL_TIMELINE_EVENTS = [];
const ORCH_STORAGE_KEY = "finresearch_orchestration_state_v4";

export function getStoredOrchestrationState() {
  return {
    agents: AGENT_ROLES,
    workflows: WORKFLOW_PRESETS,
    timeline: []
  };
}

export function saveStoredOrchestrationState(state) {
}