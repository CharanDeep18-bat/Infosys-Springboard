# API & DATABASE TECHNICAL REFERENCE

**Document Version:** 1.0.0  
**Generated Date:** November 12, 2026  
**Auditor:** Senior Software Architect  
**Scope:** Complete REST API Inventory, Contract Parity, Database DDL & Schema Mapping

---

## 1. REST API Endpoint Inventory

The backend exposes 19 production-grade endpoints grouped into five functional route modules in `Engine/app/api/routes/`:

### Group 1: System Health & Diagnostics (`health.py`)
```text
GET /health
```
- **Purpose:** Central infrastructure health probe reporting connectivity and component statuses.
- **Query Params:** None.
- **Response Contract (HTTP 200):**
  ```json
  {
    "status": "healthy",
    "version": "1.0.0",
    "database": {
      "provider": "SupabasePostgresRepository",
      "connected": true,
      "table_counts": {
        "ai_documents": 5,
        "ai_processing_jobs": 2,
        "ai_agent_runs": 20,
        "ai_financial_metrics": 94,
        "ai_red_flag_findings": 2
      }
    },
    "vector_store": {
      "provider": "ChromaVectorStore",
      "connected": true,
      "collection": "financial_chunks_local_minilm_v1",
      "total_vectors": 10
    },
    "storage": {
      "provider": "SupabaseStorage",
      "healthy": true,
      "bucket": "financial-documents"
    }
  }
  ```
- **Status Codes:** `200 OK` (all services online), `503 Service Unavailable` (database or storage unreachable).
- **Frontend Consumer:** `src/services/api.js -> getHealth()` (invoked in `App.jsx` on boot).

---

### Group 2: Workspaces & Research Sessions (`workspaces.py`)

#### `POST /workspaces`
- **Purpose:** Create a new research workspace container.
- **Request Body:** `{"name": string, "description": Optional[string]}`
- **Response Contract (HTTP 201):** `WorkspaceResponse` (`workspace_id`, `name`, `description`, `created_at`, `updated_at`, `session_count`, `document_count`).
- **Frontend Consumer:** `src/services/api.js -> createWorkspace()`.

#### `GET /workspaces`
- **Purpose:** List all available research workspaces.
- **Response Contract (HTTP 200):** `List[WorkspaceResponse]`.
- **Frontend Consumer:** `src/services/api.js -> listWorkspaces()`.

#### `GET /workspaces/{workspace_id}`
- **Purpose:** Retrieve workspace details and counts by ID.
- **Behavior:** Auto-provisions `default-workspace` if requested and not found.
- **Response Contract (HTTP 200):** `WorkspaceResponse`.
- **Frontend Consumer:** `src/services/api.js -> getWorkspace()`.

#### `POST /workspaces/{workspace_id}/sessions`
- **Purpose:** Create a new research session assigned to a workspace.
- **Request Body:** `{"title": string, "description": Optional[string]}`
- **Response Contract (HTTP 201):** `ResearchSessionResponse` (`session_id`, `workspace_id`, `title`, `description`, `status`, `created_at`, `updated_at`, `document_ids`).
- **Frontend Consumer:** `src/services/api.js -> createSession()`.

#### `GET /workspaces/{workspace_id}/sessions`
- **Purpose:** List all research sessions inside a given workspace.
- **Response Contract (HTTP 200):** `List[ResearchSessionResponse]`.
- **Frontend Consumer:** `src/services/api.js -> listWorkspaceSessions()`.

#### `GET /sessions/{session_id}`
- **Purpose:** Retrieve research session details and assigned document IDs.
- **Response Contract (HTTP 200):** `ResearchSessionResponse`.
- **Frontend Consumer:** `src/services/api.js -> getSession()`.

---

### Group 3: Financial Documents & Ingestion (`documents.py`)

#### `POST /documents/upload`
- **Purpose:** Upload, validate, store, and index a corporate financial PDF filing.
- **Content-Type:** `multipart/form-data`.
- **Parameters:**
  - `file`: UploadFile (PDF format only, $\le$ 22 MB).
  - `workspace_id`: Query string (default: `"default-workspace"`).
  - `session_id`: Optional query string.
- **Response Contract (HTTP 200 / 201):**
  ```json
  {
    "document_id": "4e5cbc6ce4844860942ef93855c2e5f9",
    "filename": "acme_cloud_technologies_sec_10k_fy25.pdf",
    "total_pages": 2,
    "characters_extracted": 1854,
    "text_preview": "UNITED STATES SECURITIES AND EXCHANGE COMMISSION...",
    "stored": true,
    "indexed": true,
    "already_exists": false,
    "chunk_count": 2,
    "chunk_preview": [...],
    "message": "PDF processed successfully. 2 pages, 1 financial tables, 2 chunks indexed.",
    "session_id": null
  }
  ```
- **Frontend Consumer:** `src/services/api.js -> uploadDocument()`.

#### `GET /documents`
- **Purpose:** List all ingested financial documents with authentic metadata.
- **Query Params:** `workspace_id` (optional filter).
- **Response Contract (HTTP 200):** `List[DocumentSummary]`.
- **Frontend Consumer:** `src/services/api.js -> listDocuments()`.

#### `GET /documents/{document_id}`
- **Purpose:** Retrieve specific document details and metadata by ID.
- **Response Contract (HTTP 200):** `DocumentSummary`.
- **Frontend Consumer:** `src/services/api.js -> getDocument()`.

#### `GET /documents/{document_id}/summary`
- **Purpose:** Return high-level extraction and indexing summary for a document.
- **Response Contract (HTTP 200):** `DocumentSummary`.

#### `GET /documents/{document_id}/file`
- **Purpose:** Stream the original uploaded PDF bytes from Supabase Storage or local filesystem.
- **Response Contract (HTTP 200):** `application/pdf` binary stream.
- **Frontend Consumer:** `src/services/api.js -> getDocumentFileUrl()`.

#### `POST /documents/seed`
- **Purpose:** Idempotently ingest preloaded corporate seed documents.
- **Response Contract (HTTP 200):** `{"seeded_count": int, "documents": List[SeedDocumentResult]}`.
- **Frontend Consumer:** `src/services/api.js -> seedDocuments()`.

#### `DELETE /documents/{document_id}`
- **Purpose:** Remove document from repository, delete vectors from vector store, and delete file from storage.
- **Response Contract (HTTP 200):** `{"deleted": true, "document_id": string}`.
- **Frontend Consumer:** `src/services/api.js -> deleteDocument()`.

---

### Group 4: Semantic Search (`search.py`)

#### `POST /search`
- **Purpose:** Multi-document semantic vector search across indexed financial passages.
- **Request Body:**
  ```json
  {
    "query": "What is the capital to risk assets ratio (CRAR)?",
    "top_k": 5,
    "document_id": null,
    "session_id": null,
    "filter_tables_only": false
  }
  ```
- **Response Contract (HTTP 200):**
  ```json
  {
    "query": "What is the capital to risk assets ratio (CRAR)?",
    "result_count": 2,
    "retriever_used": "ChromaVectorStore",
    "results": [
      {
        "chunk_id": "chunk_882ec09a_1_1",
        "text": "APEX FINANCIAL HOLDINGS GROUP - Capital Adequacy Basel III...",
        "metadata": {
          "document_id": "882ec09a897d4ce184e2a943aa980b11",
          "filename": "apex_financial_holdings_annual_report_fy25.pdf",
          "page_number": 1,
          "is_table": true
        },
        "distance": 0.3138,
        "score": 0.6862
      }
    ]
  }
  ```
- **Frontend Consumer:** `src/services/api.js -> search()`.

---

### Group 5: Multi-Agent Analysis & Orchestration (`analysis.py` & `extraction.py`)

#### `POST /documents/process` (and `POST /documents/{document_id}/process`)
- **Purpose:** Trigger the sequential multi-agent workflow (Document $\rightarrow$ Extraction $\rightarrow$ Evidence Validation $\rightarrow$ Red Flag $\rightarrow$ Persistence).
- **Request Body (Optional):**
  ```json
  {
    "document_id": "acme-test-m2-e2e",
    "filename": "acme_tech_10k_fy25.pdf",
    "workspace_id": "default-workspace",
    "session_id": null
  }
  ```
- **Response Contract (HTTP 200):**
  ```json
  {
    "job_id": "job_398a12bc",
    "document_id": "acme-test-m2-e2e",
    "status": "COMPLETED",
    "phase": "COMPLETED",
    "pages": 2,
    "chunks": 2,
    "metrics_extracted": 21,
    "red_flags": 1,
    "errors": [],
    "execution_steps": [...]
  }
  ```
- **Frontend Consumer:** `src/services/api.js -> processDocument()`.

#### `GET /documents/{document_id}/status`
- **Purpose:** Query real-time ingestion, stage progression, and agent run states.
- **Response Contract (HTTP 200):**
  ```json
  {
    "document_id": "acme-test-m2-e2e",
    "filename": "acme_tech_10k_fy25.pdf",
    "total_pages": 2,
    "total_characters": 1964,
    "chunk_count": 2,
    "indexed": true,
    "created_at": "2026-11-09T08:34:20.293764+00:00",
    "stages": {
      "DOCUMENT_AGENT": "COMPLETED",
      "EXTRACTION_AGENT": "COMPLETED",
      "RED_FLAG_AGENT": "COMPLETED"
    }
  }
  ```
- **Frontend Consumer:** `src/services/api.js -> getDocumentStatus()`.

#### `GET /documents/{document_id}/extraction`
- **Purpose:** Retrieve structured financial metrics categorized into statements and ratios.
- **Response Contract (HTTP 200):**
  ```json
  {
    "document_id": "acme-test-m2-e2e",
    "filename": "acme_tech_10k_fy25.pdf",
    "company_name": "Acme Cloud Technologies Inc.",
    "total_metrics": 21,
    "metrics": { ... },
    "income_statement": {
      "REVENUE": { "numeric_value": "4500.0000", "currency": "USD", "unit": "MILLIONS", ... }
    },
    "balance_sheet": {
      "TOTAL_ASSETS": { "numeric_value": "12000.0000", ... }
    },
    "cash_flow": {
      "OPERATING_CASH_FLOW": { "numeric_value": "1100.0000", ... }
    },
    "ratios": {
      "CURRENT_RATIO": { "numeric_value": "0.8500", "is_calculated": true, ... }
    }
  }
  ```
- **Frontend Consumer:** `src/services/api.js -> getExtractedFinancials()`.

#### `GET /documents/{document_id}/red-flags`
- **Purpose:** Retrieve detected financial red flags, forensic anomalies, and citations.
- **Response Contract (HTTP 200):**
  ```json
  {
    "document_id": "acme-test-m2-e2e",
    "total_findings": 1,
    "findings": [
      {
        "finding_id": "rf_1234abcd",
        "category": "LIQUIDITY_DETERIORATION",
        "severity": "HIGH",
        "title": "Deficient Liquidity / Current Ratio Below Par",
        "description": "Current ratio of 0.85x indicates insufficient short-term assets to cover current liabilities.",
        "detection_method": "RULE_BASED",
        "supporting_evidence": "Current Assets $1,700M vs Current Liabilities $2,000M",
        "source_page": 1,
        "requires_review": true
      }
    ]
  }
  ```
- **Frontend Consumer:** `src/services/api.js -> getDocumentRedFlags()`.

#### `GET /workflows/{run_id}/status`
- **Purpose:** Check status of an asynchronous background job.
- **Response Contract (HTTP 200):** `ai_processing_jobs` row mapping.
- **Frontend Consumer:** `src/services/api.js -> getWorkflowRunStatus()`.

---

## 2. Supabase PostgreSQL Schema Reference

The database consists of 9 normalized tables.

### Table: `ai_documents`
Primary record of uploaded and indexed filings.
- `document_id` `VARCHAR(64)` **PRIMARY KEY**
- `workspace_id` `VARCHAR(64)` (FK to `workspaces`)
- `session_id` `VARCHAR(64)` (FK to `research_sessions`)
- `user_id` `VARCHAR(64)`
- `sha256` `VARCHAR(64)` **NOT NULL UNIQUE** (Guarantees content-addressed deduplication)
- `filename` `VARCHAR(255)` **NOT NULL**
- `stored_filename` `VARCHAR(255)` **NOT NULL**
- `storage_path` `TEXT` **NOT NULL** (`supabase://...` or local path)
- `total_pages` `INTEGER` DEFAULT 0
- `total_characters` `INTEGER` DEFAULT 0
- `chunk_count` `INTEGER` DEFAULT 0
- `indexed` `INTEGER` DEFAULT 0 (1 = Indexed in vector store)
- `mime_type` `VARCHAR(64)` DEFAULT `'application/pdf'`
- `metadata` `JSONB` DEFAULT `'{}'`
- `created_at` `TIMESTAMP WITH TIME ZONE` DEFAULT `CURRENT_TIMESTAMP`
- `updated_at` `TIMESTAMP WITH TIME ZONE` DEFAULT `CURRENT_TIMESTAMP`

### Table: `ai_processing_jobs`
Durable state tracking for background worker jobs.
- `job_id` `VARCHAR(64)` **PRIMARY KEY**
- `document_id` `VARCHAR(64)` **REFERENCES** `ai_documents(document_id)` **ON DELETE CASCADE**
- `workspace_id` `VARCHAR(64)`
- `session_id` `VARCHAR(64)`
- `status` `VARCHAR(32)` (`QUEUED`, `PROCESSING`, `COMPLETED`, `FAILED`)
- `current_stage` `VARCHAR(64)`
- `error_message` `TEXT`
- `created_at` `TIMESTAMP WITH TIME ZONE` DEFAULT `CURRENT_TIMESTAMP`
- `updated_at` `TIMESTAMP WITH TIME ZONE` DEFAULT `CURRENT_TIMESTAMP`

### Table: `ai_financial_metrics`
Extracted financial line items and calculated ratios.
- `metric_id` `VARCHAR(64)` **PRIMARY KEY**
- `document_id` `VARCHAR(64)` **REFERENCES** `ai_documents(document_id)` **ON DELETE CASCADE**
- `period_type` `VARCHAR(32)` (`ANNUAL`, `QUARTERLY`, `HALF_YEAR`)
- `fiscal_year` `INTEGER` **NOT NULL**
- `statement_type` `VARCHAR(64)` (`INCOME_STATEMENT`, `BALANCE_SHEET`, `CASH_FLOW`, `KEY_RATIOS`)
- `metric_name` `VARCHAR(64)` **NOT NULL** (`REVENUE`, `CURRENT_RATIO`, etc.)
- `source_label` `VARCHAR(255)` (Raw label from report)
- `numeric_value` `NUMERIC(24, 4)` **NOT NULL** (High-precision decimal storage)
- `currency` `VARCHAR(16)` DEFAULT `'INR'`
- `unit` `VARCHAR(32)` DEFAULT `'CRORES'`
- `is_calculated` `BOOLEAN` DEFAULT `FALSE`
- `formula` `TEXT`
- `is_consolidated` `BOOLEAN` DEFAULT `TRUE`
- `created_at` `TIMESTAMP WITH TIME ZONE` DEFAULT `CURRENT_TIMESTAMP`

### Table: `ai_metric_evidence`
Verbatim grounding citations for each metric.
- `evidence_id` `VARCHAR(64)` **PRIMARY KEY**
- `metric_id` `VARCHAR(64)` **REFERENCES** `ai_financial_metrics(metric_id)` **ON DELETE CASCADE**
- `document_id` `VARCHAR(64)` **REFERENCES** `ai_documents(document_id)` **ON DELETE CASCADE**
- `page_number` `INTEGER` **NOT NULL**
- `exact_quote` `TEXT` **NOT NULL**
- `table_index` `INTEGER`
- `created_at` `TIMESTAMP WITH TIME ZONE` DEFAULT `CURRENT_TIMESTAMP`

### Table: `ai_red_flag_findings`
Detected forensic risks, accounting anomalies, and disclosure warnings.
- `finding_id` `VARCHAR(64)` **PRIMARY KEY**
- `document_id` `VARCHAR(64)` **REFERENCES** `ai_documents(document_id)` **ON DELETE CASCADE**
- `session_id` `VARCHAR(64)`
- `category` `VARCHAR(64)` (`DEBT_AND_LEVERAGE`, `LIQUIDITY_DETERIORATION`, `PROFITABILITY_DECLINE`, `AUDITOR_QUALIFICATION`, etc.)
- `severity` `VARCHAR(32)` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
- `title` `VARCHAR(255)` **NOT NULL**
- `description` `TEXT` **NOT NULL**
- `detection_method` `VARCHAR(32)` DEFAULT `'RULE_BASED'`
- `supporting_evidence` `TEXT` **NOT NULL**
- `source_page` `INTEGER` **NOT NULL**
- `requires_review` `BOOLEAN` DEFAULT `TRUE`
- `created_at` `TIMESTAMP WITH TIME ZONE` DEFAULT `CURRENT_TIMESTAMP`

### Table: `ai_agent_runs`
Audit trail of every agent execution.
- `run_id` `VARCHAR(64)` **PRIMARY KEY**
- `document_id` `VARCHAR(64)` **REFERENCES** `ai_documents(document_id)` **ON DELETE CASCADE**
- `session_id` `VARCHAR(64)`
- `agent_name` `VARCHAR(64)` **NOT NULL** (`DOCUMENT_AGENT`, `EXTRACTION_AGENT`, `RED_FLAG_AGENT`)
- `status` `VARCHAR(32)` (`STARTED`, `COMPLETED`, `FAILED`)
- `input_payload` `JSONB` DEFAULT `'{}'`
- `output_payload` `JSONB` DEFAULT `'{}'`
- `error_message` `TEXT`
- `started_at` `TIMESTAMP WITH TIME ZONE` DEFAULT `CURRENT_TIMESTAMP`
- `completed_at` `TIMESTAMP WITH TIME ZONE`

### Tables: `workspaces`, `research_sessions`, `session_documents`
Container management for multi-analyst workspaces and research projects:
- `workspaces`: `workspace_id`, `name`, `description`, `created_at`, `updated_at`.
- `research_sessions`: `session_id`, `workspace_id` (FK), `title`, `description`, `status`, `created_at`, `updated_at`.
- `session_documents`: `(session_id, document_id)` composite primary key linking documents to sessions.

---

## 3. Supabase Object Storage Architecture

- **Bucket Name:** `financial-documents` (private bucket).
- **Access Strategy:** Backend credentials exclusively (`SUPABASE_URL` + `SUPABASE_KEY`); never exposed to frontend clients.
- **Object Key Scheme:**
  $$\text{documents}/\{\text{document\_id}\}/\{\text{filename}\}$$
- **Lifecycle Implementation ([supabase_storage.py](file:///c:/Users/adina/Desktop/Infosys/document-agent/Engine/app/infrastructure/storage/supabase_storage.py)):**
  - `save_file(file_bytes, filename, document_id)`: Uploads raw bytes via REST `/storage/v1/object/...` with explicit `Content-Type: application/pdf`.
  - `get_file_bytes(document_id, object_key)`: Downloads binary PDF bytes using authenticated REST request.
  - `delete_file(document_id, object_key)`: Deletes object from the bucket.
  - `is_healthy()`: Probes bucket existence via GET `/storage/v1/bucket/{bucket}`.

