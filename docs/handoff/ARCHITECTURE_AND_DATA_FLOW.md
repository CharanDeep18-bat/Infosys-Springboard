# SYSTEM ARCHITECTURE & DATA FLOW SPECIFICATION

**Document Version:** 1.0.0  
**Generated Date:** November 12, 2026  
**Module:** Multi-Agent Financial Research System  
**Auditor:** Senior Software Architect

---

## 1. High-Level System Architecture

The application is structured into decoupled, enterprise-grade tiers: a React 19 single-page client, a Python FastAPI microservice engine, a dual-layer persistent storage tier (PostgreSQL + Supabase Object Storage), and an AI vector memory store.

```mermaid
flowchart TD
    subgraph Client ["Client Presentation Tier (React 19 + Vite 7)"]
        UI["React SPA (Port 5173)"]
        API_ADAPTER["API Client Adapter (src/services/api.js)"]
        UI --> API_ADAPTER
    end

    subgraph Gateway ["API & Application Gateway (FastAPI on Port 8000)"]
        VITE_PROXY["Vite Reverse Proxy (/api -> :8000)"]
        ROUTERS["FastAPI Endpoints (app/api/routes)"]
        API_ADAPTER --> VITE_PROXY
        VITE_PROXY --> ROUTERS
    end

    subgraph Agents ["Specialized AI Agent Tier"]
        DOC_AGENT["Agent 1: Document Intelligence Agent"]
        EXT_AGENT["Agent 2: Financial Extraction Agent"]
        VAL_NODE["Step 3: Evidence Validation Node"]
        RED_AGENT["Agent 4: Red Flag & Forensic Agent"]
        ORCHESTRATOR["LangGraph Multi-Agent Orchestrator"]
        
        ROUTERS --> ORCHESTRATOR
        ORCHESTRATOR --> DOC_AGENT
        DOC_AGENT --> EXT_AGENT
        EXT_AGENT --> VAL_NODE
        VAL_NODE --> RED_AGENT
    end

    subgraph Persistence ["Persistence & External Services Tier"]
        POSTGRES[("Supabase PostgreSQL (Port 5432)")]
        STORAGE["Supabase Storage (Bucket: financial-documents)"]
        VECTOR_PRIMARY["Qdrant Vector DB (Port 6333)"]
        VECTOR_FALLBACK["ChromaDB Vector Store (Local Disk)"]
        OPENAI["OpenAI API (gpt-4o & text-embedding-3-small)"]
        LOCAL_EMB["SentenceTransformers (all-MiniLM-L6-v2)"]

        DOC_AGENT -.-> STORAGE
        DOC_AGENT -.-> VECTOR_FALLBACK
        DOC_AGENT -.-> LOCAL_EMB
        DOC_AGENT -.-> POSTGRES

        EXT_AGENT -.-> OPENAI
        EXT_AGENT -.-> POSTGRES

        RED_AGENT -.-> OPENAI
        RED_AGENT -.-> POSTGRES
    end

    subgraph Background ["Durable Asynchronous Worker"]
        WORKER["Worker Daemon (worker.py)"]
        WORKER --> POSTGRES
        WORKER --> ORCHESTRATOR
    end
```

---

## 2. Document Processing & Ingestion Lifecycle

The complete lifecycle of a financial filing moves through eleven deterministic steps from physical upload to indexed analysis:

```mermaid
stateDiagram-v2
    [*] --> UploadReceived: POST /documents/upload
    UploadReceived --> Validation: Validate PDF format & size (< 22MB)
    Validation --> HashCheck: Compute SHA-256 Checksum
    
    HashCheck --> DuplicateFound: SHA-256 exists in ai_documents
    DuplicateFound --> VectorCheck: Verify Chunks in Vector Store
    VectorCheck --> ReturnCached: Chunks verified
    VectorCheck --> ParseLayout: Chunks missing in Vector Store
    
    HashCheck --> StoreFile: SHA-256 is new
    StoreFile --> ParseLayout: Persist to Supabase Storage / Local
    
    ParseLayout --> StructureChunk: PyMuPDF extract text, tables, pages
    StructureChunk --> GenerateEmbeddings: Target 350 tokens, 50 overlap
    GenerateEmbeddings --> VectorUpsert: OpenAI (1536d) or SentenceTransformers (384d)
    VectorUpsert --> DocumentIndexed: Commit to ChromaDB / Qdrant
    
    DocumentIndexed --> ExtractionTrigger: Trigger Sequential Pipeline
    ExtractionTrigger --> FinancialExtraction: Pull Statement Line Items
    FinancialExtraction --> DecimalCalculations: Compute Liquidity, Debt, Margins
    DecimalCalculations --> EvidenceValidation: Verify page bounds & exact quote
    
    EvidenceValidation --> ValidationFailed: Missing or out-of-bounds citations
    EvidenceValidation --> RedFlagAnalysis: Citation verification passed
    
    RedFlagAnalysis --> PersistResults: Run Deterministic Rules + LLM Disclosures
    PersistResults --> [*]: Update Job Status to COMPLETED
```

---

## 3. Sequential Multi-Agent Workflow Sequence

The workflow coordinates specialized agents sequentially to prevent hallucination, guarantee citation boundaries, and enforce deterministic mathematical accuracy:

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Client
    participant API as FastAPI Router
    participant Orchestrator as MultiAgentWorkflowOrchestrator
    participant DocAgent as Document Agent
    participant ExtAgent as Extraction Agent
    participant ValNode as Evidence Validation
    participant RedAgent as Red Flag Agent
    participant DB as Supabase PostgreSQL

    User->>API: Upload PDF (file, workspace_id, session_id)
    API->>DB: Create initial record in ai_documents (status: PENDING)
    API->>Orchestrator: run_pipeline(document_id, filename)
    
    Note over Orchestrator,DocAgent: Phase 1: Ingestion & Indexing
    Orchestrator->>DocAgent: process_pdf_upload()
    DocAgent->>DocAgent: PyMuPDF text & table extraction
    DocAgent->>DocAgent: Token-aware chunking (350 tokens)
    DocAgent->>DocAgent: Generate embeddings (384d / 1536d)
    DocAgent->>DB: Update ai_documents (indexed: 1, chunks: N)
    
    Note over Orchestrator,ExtAgent: Phase 2: Structured Metric Extraction
    Orchestrator->>ExtAgent: extract_document_financials()
    ExtAgent->>DocAgent: Retrieve document chunks
    ExtAgent->>ExtAgent: Extract statements (Income, Balance, Cash Flow)
    ExtAgent->>ExtAgent: Execute Decimal calculations (Current Ratio, D/E, Margins)
    ExtAgent->>DB: Store in ai_financial_metrics & ai_metric_evidence
    
    Note over Orchestrator,ValNode: Phase 3: Evidence Provenance Gate
    Orchestrator->>ValNode: evidence_validation_node(state)
    ValNode->>ValNode: Verify page boundaries (1 <= page <= N)
    ValNode->>ValNode: Check exact quotes against source passages
    
    Note over Orchestrator,RedAgent: Phase 4: Forensic Risk Detection
    Orchestrator->>RedAgent: analyze_document_risks()
    RedAgent->>RedAgent: Deterministic rules (Current Ratio < 1.0, D/E > 2.0)
    RedAgent->>RedAgent: Narrative disclosures (Auditor Qualifications)
    RedAgent->>DB: Store in ai_red_flag_findings
    
    Note over Orchestrator,DB: Phase 5: Atomic State Persistence
    Orchestrator->>DB: Record agent execution in ai_agent_runs
    Orchestrator->>DB: Update ai_processing_jobs (status: COMPLETED)
    Orchestrator-->>API: Return Final FinancialResearchState
    API-->>User: HTTP 200 (Completed analysis results)
```

---

## 4. Database Entity-Relationship (ER) Architecture

The relational schema in Supabase PostgreSQL enforces strict referential integrity across research workspaces, AI documents, extraction results, and forensic findings:

```mermaid
erDiagram
    WORKSPACES ||--o{ RESEARCH_SESSIONS : "contains"
    WORKSPACES ||--o{ AI_DOCUMENTS : "manages"
    RESEARCH_SESSIONS ||--o{ SESSION_DOCUMENTS : "associates"
    AI_DOCUMENTS ||--o{ SESSION_DOCUMENTS : "assigned_to"

    AI_DOCUMENTS ||--o{ AI_PROCESSING_JOBS : "triggers"
    AI_DOCUMENTS ||--o{ AI_FINANCIAL_METRICS : "extracts"
    AI_DOCUMENTS ||--o{ AI_RED_FLAG_FINDINGS : "identifies"
    AI_DOCUMENTS ||--o{ AI_AGENT_RUNS : "logs"

    AI_FINANCIAL_METRICS ||--o{ AI_METRIC_EVIDENCE : "grounded_by"

    WORKSPACES {
        string workspace_id PK
        string name
        string description
        timestamp created_at
        timestamp updated_at
    }

    RESEARCH_SESSIONS {
        string session_id PK
        string workspace_id FK
        string title
        string description
        string status
        timestamp created_at
        timestamp updated_at
    }

    SESSION_DOCUMENTS {
        string session_id PK, FK
        string document_id PK, FK
        timestamp added_at
    }

    AI_DOCUMENTS {
        string document_id PK
        string workspace_id FK
        string session_id FK
        string user_id
        string sha256 UK
        string filename
        string stored_filename
        string storage_path
        int total_pages
        int total_characters
        int chunk_count
        int indexed
        string mime_type
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }

    AI_PROCESSING_JOBS {
        string job_id PK
        string document_id FK
        string workspace_id
        string session_id
        string status
        string current_stage
        string error_message
        timestamp created_at
        timestamp updated_at
    }

    AI_FINANCIAL_METRICS {
        string metric_id PK
        string document_id FK
        string period_type
        int fiscal_year
        string statement_type
        string metric_name
        string source_label
        numeric numeric_value
        string currency
        string unit
        boolean is_calculated
        string formula
        boolean is_consolidated
        timestamp created_at
    }

    AI_METRIC_EVIDENCE {
        string evidence_id PK
        string metric_id FK
        string document_id FK
        int page_number
        string exact_quote
        int table_index
        timestamp created_at
    }

    AI_RED_FLAG_FINDINGS {
        string finding_id PK
        string document_id FK
        string session_id
        string category
        string severity
        string title
        string description
        string detection_method
        string supporting_evidence
        int source_page
        boolean requires_review
        timestamp created_at
    }

    AI_AGENT_RUNS {
        string run_id PK
        string document_id FK
        string session_id
        string agent_name
        string status
        jsonb input_payload
        jsonb output_payload
        string error_message
        timestamp started_at
        timestamp completed_at
    }
```

---

## 5. Agent Architecture & Responsibility Matrix

| Agent / Node | Primary Responsibility | Input Contract | Output Contract | Verification Rule |
| :--- | :--- | :--- | :--- | :--- |
| **Document Agent** | PDF parsing, table extraction, chunking, embedding, vector indexing | Raw PDF bytes / storage path | `DocumentUploadResponse`, Vector chunks | Zero unindexed chunks; SHA-256 idempotency |
| **Extraction Agent** | Extraction of line items, statements, Python `Decimal` ratio calculations | Indexed document chunks | `ExtractedFinancials`, `ai_financial_metrics` | Zero floating-point drift; exact Decimal math |
| **Evidence Validation** | Source quote & page number verification | Extracted metrics & citations | Validated state flag | Rejects out-of-bounds pages ($> N$) & hallucinated quotes |
| **Red Flag Agent** | Deterministic rule execution + narrative disclosure risk scanning | Extracted financials & text | `List[RedFlagFinding]` | Triggers strictly on breach thresholds; 0 false alarms on sound metrics |
| **Persistence Node** | Atomic persistence of run logs, metrics, red flags, job completion | State object | Updated database records | Atomic commits with row-level transaction safety |

