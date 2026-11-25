# Full-System Engineering Audit Report
## Multi-Agent Financial Research System

**Document Version:** 1.0.0  
**Audit Date:** 2026-11-09  
**System Architecture:** Multi-Agent Financial Intelligence Platform (FastAPI + React Vite + Supabase PostgreSQL + Supabase Storage + Qdrant Cloud / ChromaDB + OpenAI Responses API)  
**Lead Auditor:** Principal Systems Architect & Lead Software Engineer  

---

### Executive Summary

A comprehensive, end-to-end engineering audit was conducted across the entire codebase, spanning both the **Backend** (`document-agent`) and **Frontend** (`Finanical-Research`). The audit inspected data integrity, vector dimensionality, database persistence, asynchronous worker lifecycles, multi-agent LangGraph workflow orchestration, frontend UI state synchronization, and REST API contract parity.

A total of **16 concrete issues** were identified, diagnosed, and resolved directly in source code. No fabricated synthetic fallbacks or fake data defaults were tolerated.

---

### Discovered Defect Inventory

| Issue ID | Component | Severity | File(s) Affected | Description | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **AUD-001** | Embedding Provider | **P0** | `app/infrastructure/document_processing/embedder.py` | Zero-padding 384-dim SentenceTransformer embeddings with 1,152 zeroes on OpenAI 429 quota exhaustion. | **RESOLVED** |
| **AUD-002** | Vector Database | **P0** | `app/infrastructure/vector_store/qdrant.py` | Missing `get_chunks_by_document`; service fallback used hardcoded 384-dim dummy vector triggering Qdrant 400 dimension mismatch. | **RESOLVED** |
| **AUD-003** | Database Persistence | **P1** | `app/infrastructure/database/repository.py` | `SupabasePostgresRepository` delegated 100% of calls to `SQLiteRepository`, completely bypassing configured Supabase PostgreSQL. | **RESOLVED** |
| **AUD-004** | Worker Orchestration | **P1** | `app/orchestration/workflow.py`, `worker.py` | `MultiAgentWorkflowOrchestrator.run_pipeline` did not accept `job_id`, creating duplicate job records and throwing parameter errors. | **RESOLVED** |
| **AUD-005** | LLM Configuration | **P1** | `app/config.py`, `app/infrastructure/llm/provider.py` | Configured default model `gpt-6.1-sol` does not exist on OpenAI API, causing immediate 404 invocation failures. | **RESOLVED** |
| **AUD-006** | LLM Provider | **P1** | `app/infrastructure/llm/provider.py` | Silent fallback to `MockLLMProvider` on OpenAI 429 quota exhaustion, masking billing errors. | **RESOLVED** |
| **AUD-007** | Multi-Agent Workflow | **P1** | `app/orchestration/workflow.py` | Duplicate execution of Extraction Agent inside Red Flag Agent node, running full LLM extraction twice per filing. | **RESOLVED** |
| **AUD-008** | Multi-Agent Workflow | **P1** | `app/orchestration/workflow.py` | Crash when processing unseeded documents due to rigid check requiring pre-existing `default-workspace`. | **RESOLVED** |
| **AUD-009** | Evidence Validation | **P2** | `app/orchestration/workflow.py` | Superficial evidence verification checked only `page_number > 0` without validating document provenance or page bounds. | **RESOLVED** |
| **AUD-010** | Database Diagnostics | **P2** | `app/api/routes/health.py` | Health check route directly accessed SQLite private `_get_connection`, reporting zero queue statistics when using PostgreSQL. | **RESOLVED** |
| **AUD-011** | Frontend API Client | **P1** | `Finanical-Research/src/services/api.js` | Simulated upload fallback, hardcoded fake file sizes, fake checksums, and fabricated OCR/embedding model telemetry. | **RESOLVED** |
| **AUD-012** | Frontend State Sync | **P1** | `Finanical-Research/src/pages/ResearchWorkspace.jsx` | Cross-document stale state contamination: changing active document retained old extraction metrics and red flags during loading. | **RESOLVED** |
| **AUD-013** | Frontend Navigation | **P2** | `Finanical-Research/src/App.jsx`, `Sidebar.jsx` | Identifier mismatch between Sidebar navigation items (`extraction`, `evidence`, `redflags`) and `App.jsx` handler. | **RESOLVED** |
| **AUD-014** | Workspace UI Tabs | **P2** | `Finanical-Research/src/pages/ResearchWorkspace.jsx` | Blank tab view when navigating to `evidence` tab due to missing tab render condition. | **RESOLVED** |
| **AUD-015** | Document Details UI | **P2** | `Finanical-Research/src/pages/DocumentDetails.jsx` | Document chunks retained from previously viewed filing; hardcoded `"18.4 MB"` file size and fake OCR engine strings. | **RESOLVED** |
| **AUD-016** | Semantic Search UI | **P2** | `Finanical-Research/src/pages/RetrievalPreview.jsx` | Retrieval preview performed client-side simulated string matching instead of executing live vector search via FastAPI `/search`. | **RESOLVED** |

---

### Detailed Defect Analyses

#### AUD-001 (P0): Vector Dimensionality & Zero-Padding Corruption
* **File:** `app/infrastructure/document_processing/embedder.py` (lines 109–123)
* **Root Cause:** When OpenAI returned HTTP 429 quota exhaustion, `OpenAIEmbeddingProvider` caught the exception, invoked local `SentenceTransformerEmbeddingProvider` (which outputs 384-dimensional vectors), and appended `[0.0] * (1536 - 384)` (1,152 zeroes) to force a 1,536-dimensional output.
* **Impact:** Corrupted Qdrant collection geometry, distorted cosine distances, and produced meaningless similarity rankings during semantic retrieval.
* **Fix Applied:** Removed the zero-padded mock fallback. Explicitly raise a descriptive `RuntimeError` requiring valid OpenAI billing or explicit setting of `EMBEDDING_PROVIDER=sentence-transformers`.
* **Regression Test:** `tests/test_audit_repairs.py::TestAuditRepairs::test_openai_embedding_insufficient_quota_raises_explicit_error`.

#### AUD-002 (P0): Qdrant Missing `get_chunks_by_document` & 384-Dim Hardcoding
* **File:** `app/infrastructure/vector_store/qdrant.py`, `app/agents/extraction_agent/service.py`, `app/agents/red_flag_agent/service.py`
* **Root Cause:** `QdrantVectorStore` did not implement `get_chunks_by_document()`. Both downstream agents fell back to `search_chunks(query_embedding=[0.0] * 384, filters={"document_id": doc_id})`. When OpenAI 1536-dim collections were active, Qdrant returned HTTP 400 Bad Request (vector length mismatch).
* **Fix Applied:** Implemented native pagination scroll via `/collections/{name}/points/scroll` filtered on payload `document_id` without requiring any dummy embedding vector. Updated agents to use dynamic dimension fallback.
* **Regression Test:** `tests/test_audit_repairs.py::TestAuditRepairs::test_qdrant_get_chunks_by_document_scroll`.

#### AUD-003 (P1): SupabasePostgresRepository Delegating to SQLite
* **File:** `app/infrastructure/database/repository.py` (lines 1144–1390)
* **Root Cause:** `SupabasePostgresRepository` was an unpopulated wrapper delegating every single method to `self._fallback_repo = SQLiteRepository()`. Even with valid `DATABASE_URL` configured in `.env`, all records were persisted exclusively to local SQLite.
* **Fix Applied:** Implemented full SQLAlchemy 2.0 execution with psycopg3 connection pooling, parameterized queries (`text(...)`), JSONB type casting, and PostgreSQL `FOR UPDATE SKIP LOCKED` for concurrent worker queue claiming.
* **Regression Test:** Verified interface parity and fallback operations in `tests/test_audit_repairs.py`.

#### AUD-004 (P1): Worker Orchestration `job_id` Mismatch & Duplicate Rows
* **File:** `app/orchestration/workflow.py`, `worker.py`
* **Root Cause:** `worker.py` claimed an existing queued job from `ai_processing_jobs` and invoked `MultiAgentWorkflowOrchestrator.run_pipeline(..., job_id=job_id)`. However, `run_pipeline` did not accept `job_id` as an argument and created a second, redundant job row for the same document execution.
* **Fix Applied:** Added `job_id: Optional[str] = None` to `run_pipeline`. If provided, the orchestrator updates the existing in-flight job rather than spawning a duplicate.
* **Regression Test:** `tests/test_audit_repairs.py::TestAuditRepairs::test_sqlite_repository_stale_job_recovery_and_stats`.

#### AUD-005 & AUD-006 (P1): Non-Existent LLM Model & Silent Mock Fallback
* **File:** `app/config.py`, `app/infrastructure/llm/provider.py`
* **Root Cause:** Config defaulted `llm_model` to `gpt-6.1-sol`, which is non-existent. On 429 quota exhaustion, `OpenAILLMProvider` silently generated synthetic mock completions instead of failing loudly.
* **Fix Applied:** Changed default model to `gpt-4o`. Removed silent mock fallback; now raises explicit `RuntimeError` prompting the user to check billing or set `LLM_PROVIDER=mock`.
* **Regression Test:** `tests/test_llm_provider.py::TestLLMProvider::test_openai_quota_exhausted_raises_explicit_error`.

#### AUD-007 (P1): Duplicate Extraction Agent Invocation
* **File:** `app/orchestration/workflow.py` (lines 240–250)
* **Root Cause:** `red_flag_agent_node` invoked `ext_service.extract_document_financials()` a second time, repeating parsing, LLM generation, and metric calculation that had already completed in `extraction_agent_node`.
* **Fix Applied:** Threaded the extracted model instance directly through `state.extracted_financials["_model"]`, allowing `red_flag_agent_node` to reuse existing metrics immediately.

#### AUD-009 (P2): Superficial Evidence Validation
* **File:** `app/orchestration/workflow.py` (lines 206–225)
* **Root Cause:** Evidence validation only verified `page_number > 0`, ignoring document mismatch, out-of-bounds page numbers, or missing citation text.
* **Fix Applied:** Enhanced validation node to enforce:
  1. Provenance matching (`citation.document_id == state.document_id`).
  2. Page bounds verification (`1 <= page_number <= state.total_pages`).
  3. Formula integrity for calculated ratios.
  4. Structured agent execution step logging and stage progress updates.
* **Regression Test:** `tests/test_audit_repairs.py::TestAuditRepairs::test_evidence_validation_rejects_empty_citations` and `test_evidence_validation_passes_valid_citations`.

#### AUD-011, AUD-012, AUD-013, AUD-014 (P1–P2): Frontend State, Navigation & Parity
* **Files:** `Finanical-Research/src/services/api.js`, `App.jsx`, `ResearchWorkspace.jsx`, `Sidebar.jsx`, `RetrievalPreview.jsx`
* **Root Causes:**
  - Mock fallback in API client generated synthetic responses when the backend was restarting.
  - Stale state persisted when switching filings in `ResearchWorkspace.jsx`.
  - Sidebar identifiers (`extraction`, `evidence`, `redflags`) did not match `App.jsx` page routing.
  - `RetrievalPreview.jsx` performed local string matching instead of invoking FastAPI `/search`.
* **Fixes Applied:**
  - Standardized API client with `AbortController` timeouts, authentic HTTP error handling, and zero mock fallbacks.
  - Implemented immediate state clearing (`setExtractedData(null); setRedFlags([]);`) and active document cancellation tokens.
  - Aligned navigation routing across `Sidebar.jsx`, `App.jsx`, and `ResearchWorkspace.jsx`.
  - Wired `RetrievalPreview.jsx` directly to `api.search()`.

