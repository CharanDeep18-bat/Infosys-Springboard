# MASTER PROJECT CONTEXT: MULTI-AGENT FINANCIAL RESEARCH SYSTEM

**Document Version:** 1.0.0  
**Generated Date:** November 12, 2026  
**Auditor:** Senior Software Architect & Technical Documentation Engineer  
**Scope:** Complete End-to-End System Handoff (Frontend + Backend + Database + Vector Store + AI Pipeline)

---

## 1. Executive Summary & Purpose

The **Multi-Agent Financial Research System** is an institutional-grade, multi-agent artificial intelligence platform designed to augment financial analysis of corporate filings, annual reports (10-K, 10-Q), statutory disclosures, and earnings call transcripts.

### The Problem
Finance students, MBA candidates, equity research associates, and investment analysts spend up to 70% of their research workflow manually reading lengthy filings, extracting tabular financial metrics, cross-referencing notes to accounts, normalizing accounting differences, and checking for forensic red flags. This manual workflow is tedious, prone to human error, and difficult to scale across peer groups.

### The Solution
The system deploys a team of specialized, deterministic and AI-powered agents collaborating through a sequential LangGraph workflow. Upon document ingestion:
1. **Document Agent:** Validates, stores, parses layout/tables, chunks, generates embeddings, and indexes filings into a vector database.
2. **Extraction Agent:** Automatically extracts structured income statement, balance sheet, and cash flow metrics, performing high-precision Python `Decimal` financial ratio calculations.
3. **Evidence Validation Layer:** Enforces strict provenance and source grounding, rejecting ungrounded or out-of-bounds citations.
4. **Red Flag Agent:** Executes a hybrid risk detection engine combining deterministic financial rules (leverage, liquidity, profitability, cash flow divergence) and narrative disclosure analysis (auditor qualifications, going-concern warnings, restatements).
5. **Durable Persistence Layer:** Stores all metrics, findings, execution states, and audit trails in Supabase PostgreSQL.

---

## 2. Project Directory Structure & Organization

The codebase is organized into two primary root modules inside `document-agent/`:

```text
document-agent/
├── Engine/                               # Python FastAPI Backend & Agent Service Layer
│   ├── app/                              # Core application source code
│   │   ├── agents/                       # Specialized AI agent implementations
│   │   │   ├── document_agent/           # Document ingestion, parsing, chunking, indexing
│   │   │   ├── extraction_agent/         # Financial metric extraction, normalizer, Decimal ratios
│   │   │   └── red_flag_agent/           # Rule engine, disclosure analyzer, risk detection
│   │   ├── api/                          # FastAPI route handlers and controllers
│   │   │   └── routes/                   # health, documents, workspaces, analysis, extraction, search
│   │   ├── infrastructure/               # External adapters and infrastructure interfaces
│   │   │   ├── database/                 # SQLAlchemy 2.0, repository implementations, models
│   │   │   ├── document_processing/      # PDF parser, table extractor, token chunker, embedder
│   │   │   ├── llm/                      # OpenAI provider, Mock provider, structured output parser
│   │   │   ├── storage/                  # Supabase Storage & local filesystem storage adapters
│   │   │   └── vector_store/             # Qdrant REST client & persistent ChromaDB adapter
│   │   ├── orchestration/                # MultiAgentWorkflowOrchestrator, LangGraph state & nodes
│   │   └── schemas/                      # Typed Pydantic v2 domain schemas and API contracts
│   ├── chroma_db/                        # Persistent ChromaDB vector storage directory
│   ├── docs/                             # Architecture specifications, audits, repair plans
│   │   └── handoff/                      # Central handoff and migration documentation
│   ├── migrations/                       # Alembic database migration scripts
│   ├── scripts/                          # Verification, seed generation, and ingestion scripts
│   ├── seed_documents/                   # Preloaded corporate financial PDF filings (5 filings)
│   ├── uploads/                          # Local document upload directory (when STORAGE_PROVIDER=local)
│   ├── venv/                             # Python 3.14.6 virtual environment
│   ├── .env                              # Active environment configuration (never committed)
│   ├── .env.example                      # Configuration template with all variable declarations
│   ├── alembic.ini                       # Alembic migration configuration
│   ├── main.py                           # FastAPI application entry point
│   ├── requirements.txt                  # Backend Python dependencies
│   └── worker.py                         # Durable background job processor (polls PostgreSQL)
│
└── Frontend/                             # React 19 + Vite 7 Single Page Application
    ├── dist/                             # Compiled production build artifacts
    ├── node_modules/                     # Node dependencies
    ├── src/                              # React application source code
    │   ├── components/                   # UI components, modals, sidebar, header, viewers
    │   │   ├── chat/                     # Research chat, citation viewer, source panels
    │   │   ├── orchestration/            # Execution timeline, agent overview grid, workflow diagrams
    │   │   ├── report/                   # PDF report preview, config modals, export dialogs
    │   │   └── ui/                       # Base design system: Button, Card, Badge, Table, Tabs, Dialog
    │   ├── data/                         # Document, seed, and orchestration initial data structures
    │   ├── pages/                        # View components: Dashboard, WorkspaceDirectory, DocumentLibrary,
    │   │                                 # DocumentDetails, ResearchWorkspace, OrchestrationView, ReportView
    │   ├── services/                     # Central API client adapter (api.js)
    │   ├── App.jsx                       # Main application state, theme, route switching
    │   ├── index.css                     # Tailwind CSS and global styling tokens
    │   └── main.jsx                      # React 19 root mounting entry point
    ├── .env                              # Frontend environment (VITE_API_BASE_URL=/api)
    ├── package.json                      # Frontend dependencies and scripts
    └── vite.config.js                    # Vite configuration with /api reverse proxy to port 8000
```

---

## 3. Requirements & Milestone Traceability

The project roadmap is governed by a 4-milestone plan defined in the foundational project specification:

### Milestone 1 (Week 1–2): Ingestion & Document Intelligence
- **Status:** **COMPLETE & VERIFIED**
- Study financial document formats (annual reports, SEC 10-K filings, earnings transcripts).
- Design multi-agent system architecture, data models, and database schema.
- Implement research workspace and session management.
- Build Document Agent: upload, PyMuPDF parsing, structure-aware chunking, embeddings, and vector indexing.
- Pre-load and verify at least 3–4 seed corporate financial documents (5 seed documents implemented and verified).

### Milestone 2 (Week 3–4): Financial Extraction & Red Flag Analysis
- **Status:** **COMPLETE & VERIFIED**
- Build Extraction Agent: automated extraction of Income Statement, Balance Sheet, and Cash Flow metrics.
- Implement exact Python `Decimal` financial ratio computations (Current Ratio, Debt-to-Equity, Profit Margins, ROE, FCF).
- Build Red Flag Agent: automated scanning for leverage stress, liquidity deficits, cash flow divergence, and auditor qualifications.
- Build Multi-Agent Orchestration Layer: coordinates Document, Extraction, and Red Flag agents sequentially.
- Test and validate agent outputs on seed financial documents for accuracy and source faithfulness.

### Milestone 3 (Week 5–6): Comparison & Conversational Research
- **Status:** **PLANNED / DEFERRED**
- Build Comparison Agent: cross-reference extracted metrics across multiple companies for side-by-side benchmarking.
- Build Research Agent: handle multi-part user queries with multi-step retrieval, step-by-step reasoning, and source citations.
- Develop conversational research interface in Frontend.
- Begin Report Agent development: Executive Summary and Key Financials section compilation.

### Milestone 4 (Week 7–8): Analyst Report Generation & System Hardening
- **Status:** **PLANNED / DEFERRED**
- Complete Report Agent: compile findings into a structured analyst-style PDF report exportable for stakeholders.
- End-to-end multi-agent evaluation, citation audit, performance tuning, and final documentation.

---

## 4. Key Architectural & Implementation Decisions

1. **Deterministic Financial Computations:**
   Financial ratios (e.g., Current Ratio, Debt-to-Equity, Margins) must **never** be estimated or hallucinated by LLMs. All ratio formulas are executed purely in Python using the `decimal.Decimal` module to prevent IEEE-754 binary floating-point rounding errors.

2. **Strict Evidence Provenance (Zero Hallucination):**
   Every extracted metric and detected red flag requires an explicit, verifiable `SourceCitation` containing the exact source page number ($1 \le \text{page} \le N$) and verbatim text quote. Citations lacking verifiable backing are flagged or rejected by `evidence_validation_node`.

3. **Supabase PostgreSQL as Authoritative Database:**
   All persistent state (`ai_documents`, `ai_processing_jobs`, `ai_financial_metrics`, `ai_red_flag_findings`, `ai_agent_runs`) resides in Supabase PostgreSQL via connection pooling. A local SQLite fallback is preserved exclusively for offline testing and isolated unit tests.

4. **Dual Vector Database & Automatic Fallback:**
   The primary vector store is Qdrant (via native REST client). When Qdrant is unreachable at `http://localhost:6333`, the factory automatically falls back to persistent ChromaDB (`chroma_db/`) with diagnostic logging, allowing uninterrupted local development.

5. **Dual Embedding Engine:**
   - Production Profile: OpenAI `text-embedding-3-small` (1536-dimensional vectors).
   - Local/Offline Profile: HuggingFace SentenceTransformers `all-MiniLM-L6-v2` (384-dimensional vectors).

6. **Durable Asynchronous Job Processing:**
   Document processing can execute synchronously through direct API invocation or asynchronously through `worker.py`. The background worker uses atomic PostgreSQL row locking (`FOR UPDATE SKIP LOCKED`) and automatic crash recovery to resume stalled jobs.

---

## 5. Technology Stack Summary

| Layer | Component | Technology / Library | Version / Profile |
| :--- | :--- | :--- | :--- |
| **Frontend** | Framework | React | 19.1.0 |
| | Build Tool | Vite | 7.3.7 |
| | Styling | Tailwind CSS | Custom Institutional Theme |
| | Icons | Lucide React | 0.468.0 |
| | Notifications | React Hot Toast | 2.6.1 |
| | Router | React Router DOM | 7.18.4 (with internal tab/subview state) |
| **Backend** | API Framework | FastAPI | >= 0.115.0 |
| | Web Server | Uvicorn (standard) | >= 0.30.0 |
| | Language | Python | 3.14.6 (`Engine/venv`) |
| | Data Validation | Pydantic / Pydantic Settings | >= 2.10.0 |
| | Database ORM | SQLAlchemy 2.0 / psycopg3 | >= 2.0.0 / >= 3.2.0 |
| | Migrations | Alembic | >= 1.13.0 |
| | PDF Parsing | PyMuPDF (`pymupdf`, `fitz`) | >= 1.24.0 |
| | Vector Database | Qdrant (REST) / ChromaDB | chromadb >= 0.5.0 |
| | Local Embeddings| SentenceTransformers / PyTorch | sentence-transformers >= 3.0.0 |
| | Cloud LLM / Emb| OpenAI Python SDK / httpx | openai >= 1.50.0 / httpx >= 0.27.0 |
| | Cloud Storage | Supabase Python SDK / REST | supabase >= 2.0.0 |

