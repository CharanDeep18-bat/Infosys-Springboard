# KNOWN ISSUES, TECHNICAL DEBT & DEVELOPMENT ROADMAP

**Document Version:** 1.0.0  
**Generated Date:** November 12, 2026  
**Auditor:** Senior Software Architect  
**Scope:** Prioritized Technical Debt (P0–P3), Root Causes, Recommended Remediations, Next Steps

---

## 1. Prioritized Technical Debt & Issues

### Priority 0: Critical Correctness & Architecture Risks

#### Issue P0-1: Embedding Dimension Mismatch Risk
- **Impact:** System failure during vector search if vectors generated with one model are queried using another, or if ChromaDB and Qdrant use conflicting dimensions.
- **Root Cause:**
  - Production profile: OpenAI `text-embedding-3-small` generates **1536-dimensional** vectors.
  - Local/offline fallback profile: SentenceTransformers `all-MiniLM-L6-v2` generates **384-dimensional** vectors.
  - If a document is indexed into ChromaDB with 384d vectors and the backend switches to `EMBEDDING_PROVIDER=openai` (1536d), query embeddings cannot be compared against 384d vectors.
- **Relevant Files:**
  - `Engine/app/infrastructure/document_processing/embedder.py`
  - `Engine/app/infrastructure/vector_store/chroma.py`
  - `Engine/app/config.py`
- **Recommended Remediation:**
  - Enforce collection namespacing by dimension:
    - `financial_chunks_local_minilm_v1` (explicitly for 384d).
    - `financial_chunks_openai_te3small_v1` (explicitly for 1536d).
  - Add startup validation: assert that the active collection dimension matches `settings.embedding_dimension`. If a mismatch is detected, log an explicit warning or use the namespaced collection for that model.

#### Issue P0-2: OpenAI Credit Quota Exhaustion in Live Environment
- **Impact:** During live LLM calls, if the OpenAI billing quota is exhausted, cloud reasoning fails with `429 insufficient_quota`.
- **Root Cause:** The active OpenAI account does not have sufficient prepaid API credits for GPT-4o inference.
- **Current Behavior:** The system gracefully catches quota exhaustion, logs a clean diagnostic warning, and falls back to deterministic extraction and rules so the pipeline never crashes.
- **Relevant Files:**
  - `Engine/app/infrastructure/llm/provider.py`
  - `Engine/app/agents/extraction_agent/extractor.py`
  - `Engine/app/agents/red_flag_agent/analyzer.py`
- **Recommended Remediation:**
  - Ensure the user's OpenAI billing plan has active credits, OR configure `LLM_PROVIDER=mock` for completely offline development, OR integrate Google Gemini API as an alternative provider (`LLM_PROVIDER=gemini`).

---

### Priority 1: Core Functionality & Access Control

#### Issue P1-1: Multi-Tenant Workspace Isolation & `default-workspace` Auto-Provisioning
- **Impact:** Single-tenant development works seamlessly, but multi-tenant enterprise isolation is not yet fully locked down.
- **Root Cause:**
  - `default-workspace` is automatically created on-the-fly when requested by frontend endpoints (`app/api/routes/workspaces.py`).
  - Documents uploaded without an explicit `workspace_id` are defaulted to `"default-workspace"`.
  - While `test_multi_document_isolation.py` proves that vector searches filtered by `document_id` are isolated, workspace-level RBAC (user ownership of workspaces) is not yet implemented.
- **Relevant Files:**
  - `Engine/app/api/routes/workspaces.py`
  - `Engine/app/api/routes/documents.py`
  - `Engine/app/orchestration/workflow.py`
- **Recommended Remediation:**
  - Introduce `user_id` authorization tokens on workspace and session creation.
  - Disallow automatic fallback to `default-workspace` in production mode (`APP_ENV=production`), requiring explicit workspace selection.

#### Issue P1-2: Supabase Storage Row-Level Security (RLS)
- **Impact:** Uploaded document files are stored in a private bucket (`financial-documents`), but object isolation is handled by backend code rather than database RLS policies.
- **Root Cause:** The backend connects to Supabase Storage using service credentials. Any caller with backend API access can download documents via `GET /documents/{document_id}/file`.
- **Relevant Files:**
  - `Engine/app/infrastructure/storage/supabase_storage.py`
  - `Engine/app/api/routes/documents.py`
- **Recommended Remediation:**
  - When user authentication is introduced in Milestone 3/4, attach signed storage URLs with time-limited expirations (`create_signed_url`) rather than streaming directly from backend storage.

---

### Priority 2: Incomplete Features & User Experience

#### Issue P2-1: Scanned Document OCR Ingestion
- **Impact:** Scanned PDF filings containing non-selectable rasterized images (e.g., photocopied statutory filings) will yield 0 extracted characters.
- **Root Cause:** PyMuPDF (`fitz`) extracts digital text and vector tables natively. It does not perform optical character recognition on pure images unless Tesseract or OpenAI PDF Vision is configured.
- **Relevant Files:**
  - `Engine/app/infrastructure/document_processing/parser.py`
  - `Engine/app/config.py` (`openai_enable_pdf_vision`)
- **Recommended Remediation:**
  - Enable `openai_enable_pdf_vision=true` or install `pytesseract` to handle scanned legacy filings.

#### Issue P2-2: Real-time Pipeline Execution Streaming (WebSocket / SSE)
- **Impact:** Currently, frontend monitors pipeline status via polling (`GET /documents/{document_id}/status`).
- **Root Cause:** Server-Sent Events (SSE) or WebSockets have not been added to the FastAPI router.
- **Relevant Files:**
  - `Engine/app/api/routes/analysis.py`
  - `Frontend/src/pages/DocumentDetails.jsx`
- **Recommended Remediation:**
  - Add an SSE endpoint: `GET /documents/{document_id}/events` streaming agent stage events directly to the frontend timeline.

#### Issue P2-3: Mock Data in Deferred Milestone Pages
- **Impact:** `ConversationalResearch.jsx` and `ReportView.jsx` currently render mock research chats and report templates.
- **Root Cause:** Milestone 3 (Research Agent) and Milestone 4 (Report Agent) were explicitly deferred in the original roadmap.
- **Relevant Files:**
  - `Frontend/src/pages/ConversationalResearch.jsx`
  - `Frontend/src/pages/ReportView.jsx`
  - `Frontend/src/data/researchChatData.js`
  - `Frontend/src/data/reportData.js`
- **Recommended Remediation:**
  - Wire `ConversationalResearch.jsx` to the Milestone 3 Research Agent backend once implemented.

---

### Priority 3: Maintainability & Optimization

#### Issue P3-1: Frontend Vendor Bundle Size Warning
- **Impact:** `vite build` emits a non-fatal warning: `(!) Some chunks are larger than 500 kB after minification: dist/assets/index-DhJD_oQ3.js (542 kB)`.
- **Root Cause:** Lucide React and React 19 packages are bundled into a single entry chunk.
- **Relevant Files:**
  - `Frontend/vite.config.js`
- **Recommended Remediation:**
  - Configure Rollup manual chunks in `vite.config.js`:
    ```javascript
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom', 'react-router-dom'],
            icons: ['lucide-react']
          }
        }
      }
    }
    ```

---

## 2. Top Five Recommended Next Actions for Gemini

When continuing development, the next AI assistant should execute tasks in the following exact sequence:

1. **Maintain Vector Store & Embedding Model Alignment:**
   Ensure `EMBEDDING_PROVIDER` (OpenAI 1536d vs SentenceTransformers 384d) is deliberately chosen and matched with its namespaced collection name before uploading new documents.

2. **Implement Milestone 3: Comparison Agent:**
   Create `Engine/app/agents/comparison_agent/` to cross-reference extracted metrics across multiple companies (e.g., comparing Acme Cloud vs Zenith Energy vs Infosys) for side-by-side benchmarking.

3. **Implement Milestone 3: Conversational Research Agent:**
   Create `Engine/app/agents/research_agent/` to answer multi-part financial questions using multi-hop retrieval and step-by-step reasoning with exact citations, wiring it to `ConversationalResearch.jsx`.

4. **Add Real-time Server-Sent Events (SSE) for Pipeline Execution:**
   Implement `GET /documents/{document_id}/events` in FastAPI and connect `AgentPipelineTracker.jsx` in the frontend for live stage progression feedback without polling.

5. **Build Milestone 4: Report Agent & PDF Export:**
   Create `Engine/app/agents/report_agent/` to compile executive summaries, financial tables, red flag findings, and outlook into structured analyst-style PDF documents, wiring it to `ReportView.jsx`.

