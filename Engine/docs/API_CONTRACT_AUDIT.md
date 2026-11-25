# API Contract Audit & Integration Matrix
## FastAPI Backend (`document-agent`) ↔ React Frontend (`Finanical-Research`)

**Document Version:** 1.0.0  
**Audit Date:** 2026-11-09  
**Base URL:** `http://localhost:8000` (Direct) | `/api` (Vite Proxy)  

---

### Endpoint Matrix & Parity Verification

| Method | Path | FastAPI Route Handler | Frontend API Method (`api.js`) | Request Model / Params | Response Model | Parity Status |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| `GET` | `/health` | `app.api.routes.health:health_check` | `api.getHealth()` | None | Health diagnostics JSON (status, DB, storage, vector store, embedding, LLM, worker) | **FULL PARITY** |
| `GET` | `/workspaces` | `app.api.routes.workspaces:list_workspaces` | `api.listWorkspaces()` | None | `List[WorkspaceSummaryResponse]` | **FULL PARITY** |
| `POST` | `/workspaces` | `app.api.routes.workspaces:create_workspace` | `api.createWorkspace(payload)` | `CreateWorkspaceRequest` | `WorkspaceResponse` | **FULL PARITY** |
| `GET` | `/workspaces/{id}` | `app.api.routes.workspaces:get_workspace` | `api.getWorkspace(id)` | Path `id` | `WorkspaceResponse` | **FULL PARITY** |
| `GET` | `/workspaces/{id}/sessions` | `app.api.routes.workspaces:list_workspace_sessions` | `api.listWorkspaceSessions(id)` | Path `id` | `List[SessionResponse]` | **FULL PARITY** |
| `POST` | `/workspaces/{id}/sessions` | `app.api.routes.workspaces:create_session` | `api.createSession(wsId, payload)` | Path `id`, `CreateSessionRequest` | `SessionResponse` | **FULL PARITY** |
| `GET` | `/sessions/{id}` | `app.api.routes.workspaces:get_session` | `api.getSession(id)` | Path `id` | `SessionResponse` | **FULL PARITY** |
| `POST` | `/sessions/{id}/documents` | `app.api.routes.workspaces:add_document_to_session` | `api.addDocumentToSession(sId, docId)` | `AssociateDocumentRequest` | `SessionResponse` | **FULL PARITY** |
| `GET` | `/documents` | `app.api.routes.documents:list_documents` | `api.listDocuments(workspaceId)` | Query `workspace_id` (optional) | `List[DocumentRecordResponse]` | **FULL PARITY** |
| `POST` | `/documents/upload` | `app.api.routes.documents:upload_pdf` | `api.uploadDocument(file, ...)` | `UploadFile` (multipart/form-data) | `DocumentUploadResponse` | **FULL PARITY** |
| `GET` | `/documents/{id}` | `app.api.routes.documents:get_document` | `api.getDocument(id)` | Path `id` | `DocumentRecordResponse` | **FULL PARITY** |
| `DELETE`| `/documents/{id}` | `app.api.routes.documents:delete_document` | `api.deleteDocument(id)` | Path `id` | `{"deleted": true, "document_id": id}` | **FULL PARITY** |
| `GET` | `/documents/{id}/file` | `app.api.routes.documents:get_document_file` | Direct PDF URL `${API_BASE}/documents/${id}/file` | Path `id` | PDF Binary Stream (`application/pdf`) | **FULL PARITY** |
| `POST` | `/search` | `app.api.routes.search:semantic_search` | `api.search(query, ...)` | `SearchRequest` (JSON) | `SearchResponse` (results, total_hits) | **FULL PARITY** |
| `GET` | `/documents/{id}/financials` | `app.api.routes.extraction:get_document_financials` | `api.getExtractedFinancials(id)` | Path `id` | Extracted financials JSON (metrics, GAAP statement, citations) | **FULL PARITY** |
| `GET` | `/documents/{id}/red-flags` | `app.api.routes.analysis:get_red_flags` | `api.getRedFlags(id)` | Path `id` | `List[RedFlagFinding]` (rule-based + LLM disclosures) | **FULL PARITY** |
| `POST` | `/documents/{id}/execute-pipeline` | `app.api.routes.analysis:trigger_analysis_pipeline` | `api.triggerAnalysisPipeline(id)` | Path `id`, query `session_id` | Processing job tracking JSON (`job_id`, status) | **FULL PARITY** |

---

### Key Contract Guarantees

1. **Zero Fabricated Fields:** Missing values from backend are preserved as `null` or formatted as `"Unknown"` instead of hallucinating values like `"18.4 MB"` or `"Financial-OCR-TableNet v2.4"`.
2. **Authenticated File Access:** PDF retrieval uses the backend endpoint `/documents/{id}/file`, which retrieves the file securely from either Supabase Storage or local disk and streams it with headers:
   - `Content-Type: application/pdf`
   - `Content-Disposition: inline; filename="..."`
3. **Multi-Agent State Pipeline:** When `/documents/{id}/execute-pipeline` is called:
   - If an asynchronous worker is running, a job is inserted into `ai_processing_jobs` with status `QUEUED`.
   - The worker claims it via `FOR UPDATE SKIP LOCKED`, sets status to `PROCESSING`, executes `MultiAgentWorkflowOrchestrator.run_pipeline(..., job_id=job_id)`, and sets status to `COMPLETED`.
   - If the worker is offline, the endpoint falls back to synchronous inline orchestration and updates the job immediately.

