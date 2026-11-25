# ENVIRONMENT, CONFIGURATION & OPERATIONS MANUAL

**Document Version:** 1.0.0  
**Generated Date:** November 12, 2026  
**Auditor:** Senior Software Architect  
**Scope:** Configuration Inventory, Startup Commands, Migration Execution, Troubleshooting

---

## 1. Environment Variables Specification

> [!IMPORTANT]
> All credentials and connection secrets are strictly redacted in this document. Only variable names and architectural purposes are documented.

| Variable Name | Used By | Architectural Purpose | Required | Active Profile Status |
| :--- | :--- | :--- | :---: | :--- |
| `APP_ENV` | `app/config.py` | Runtime profile (`development`, `staging`, `production`) | No | `development` |
| `DEBUG` | `app/config.py` | FastAPI debug mode flag | No | `true` |
| `PORT` | `app/config.py` | Backend Uvicorn HTTP server port | No | `8000` |
| `DATABASE_URL` | `app/infrastructure/database/` | Supabase PostgreSQL pooled connection URL (`postgresql+psycopg://...`) | Yes (Prod) | Configured in `Engine/.env` |
| `SQLITE_DB_PATH` | `app/infrastructure/database/` | Local SQLite file path for offline/unit test isolation | No | `documents.db` |
| `STORAGE_PROVIDER` | `app/infrastructure/storage/` | Document storage driver (`local` or `supabase`) | Yes | `supabase` (Production) / `local` |
| `UPLOAD_DIR` | `app/infrastructure/storage/` | Local filesystem directory for file storage | No | `uploads` |
| `SUPABASE_URL` | `app/infrastructure/storage/` | Supabase project REST endpoint | Yes (Cloud) | Configured in `Engine/.env` |
| `SUPABASE_KEY` | `app/infrastructure/storage/` | Supabase service-role/anon API key | Yes (Cloud) | Configured in `Engine/.env` |
| `SUPABASE_STORAGE_BUCKET` | `app/infrastructure/storage/` | Target private storage bucket name | Yes (Cloud) | `financial-documents` |
| `VECTOR_STORE_TYPE` | `app/infrastructure/vector_store/`| Vector store driver (`qdrant`, `chroma`, `auto`) | Yes | `auto` (ChromaDB fallback active) |
| `QDRANT_URL` | `app/infrastructure/vector_store/`| Qdrant server REST host and port | No | `http://localhost:6333` |
| `QDRANT_API_KEY` | `app/infrastructure/vector_store/`| Qdrant Cloud API authentication token | No | Redacted / Optional for local |
| `QDRANT_COLLECTION` | `app/infrastructure/vector_store/`| Collection name for 1536d OpenAI vectors | No | `financial_chunks_openai_te3small_v1` |
| `CHROMA_DB_DIR` | `app/infrastructure/vector_store/`| Persistent disk directory for ChromaDB | No | `chroma_db` |
| `CHROMA_COLLECTION` | `app/infrastructure/vector_store/`| Collection name for 384d MiniLM vectors | No | `financial_chunks_local_minilm_v1` |
| `EMBEDDING_PROVIDER` | `app/infrastructure/document_processing/` | Embedding engine (`openai` or `sentence-transformers`) | Yes | `openai` (Prod) / `sentence-transformers` |
| `EMBEDDING_MODEL` | `app/infrastructure/document_processing/` | Model identifier | No | `text-embedding-3-small` |
| `EMBEDDING_DIMENSION`| `app/infrastructure/document_processing/` | Vector dimensionality ($1536$ or $384$) | Yes | `1536` (OpenAI) / `384` (MiniLM) |
| `LLM_PROVIDER` | `app/infrastructure/llm/` | LLM driver (`openai`, `mock`, `gemini`) | Yes | `openai` (Cloud) / `mock` (Offline) |
| `OPENAI_API_KEY` | `app/infrastructure/llm/` | OpenAI API authentication token | Yes (OpenAI)| Configured in `Engine/.env` |
| `LLM_MODEL` | `app/infrastructure/llm/` | Primary reasoning model | No | `gpt-4o` |
| `LLM_REASONING_EFFORT`| `app/infrastructure/llm/` | Reasoning effort budget (`low`, `medium`, `high`) | No | `high` |
| `OPENAI_ENABLE_PDF_VISION` | `app/infrastructure/document_processing/` | Vision API fallback for scanned PDFs | No | `false` |
| `SEED_DOCS_DIR` | `app/infrastructure/document_processing/` | Directory containing corporate seed filings | No | `seed_documents` |
| `MAX_FILE_SIZE` | `app/agents/document_agent/` | Maximum permissible upload size ($22\text{ MB}$) | No | `23068672` |
| `CHUNK_TARGET_TOKENS` | `app/infrastructure/document_processing/` | Target size per text chunk | No | `350` |
| `CHUNK_OVERLAP_TOKENS`| `app/infrastructure/document_processing/` | Overlapping token context between chunks | No | `50` |
| `WORKER_POLL_SECONDS` | `worker.py` | Polling frequency for queued database jobs | No | `3` |
| `WORKER_MAX_RETRIES` | `worker.py` | Maximum job retry attempts before failing | No | `3` |
| `VITE_API_BASE_URL` | `Frontend/.env` | Client-side API root path routed via Vite | Yes | `/api` |

---

## 2. System Runtime Requirements

- **Python Runtime:** Python 3.14.6 (Virtual environment: `Engine/venv`).
- **Node.js Runtime:** Node.js v24.22.1 with npm 11.19.1.
- **Operating System:** Windows PowerShell (cmdlet compatible) or Unix Bash.
- **Relational Database:** Supabase PostgreSQL with `pgvector` and SSL enabled (`sslmode=require`).
- **Cloud Object Storage:** Supabase Storage bucket `financial-documents`.

---

## 3. Operational Startup Guide

### Step 1: Start Backend API Gateway
Open a terminal in `Engine/`:
```powershell
cd C:\Users\adina\Desktop\Infosys\document-agent\Engine
.\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```
- **Healthy Log Output:**
  ```text
  [INFO] document-agent: Starting Multi-Agent Financial Research System v0.1.0 in development mode...
  [INFO] app.infrastructure.database.repository: SupabasePostgresRepository connected to PostgreSQL: aws-0-ap-south-1.pooler.supabase.com:5432/postgres?sslmode=require
  [INFO] app.infrastructure.vector_store.factory: Qdrant not reachable at http://localhost:6333. Falling back to persistent ChromaDB.
  [INFO] document-agent: Active vector store provider: ChromaVectorStore
  INFO: Application startup complete. Uvicorn running on http://127.0.0.1:8000
  ```

### Step 2: Start Background Job Worker (Optional for Async Processing)
Open a separate terminal in `Engine/`:
```powershell
cd C:\Users\adina\Desktop\Infosys\document-agent\Engine
.\venv\Scripts\python.exe worker.py
```
- **Healthy Log Output:**
  ```text
  [INFO] [worker] Multi-Agent Persistent Job Worker Online
  [INFO] [worker] Polling Database: SupabasePostgresRepository
  [INFO] [worker] Poll Interval: 3s | Max Retries: 3
  [INFO] [worker] Waiting for queued financial document processing jobs...
  ```

### Step 3: Start Frontend Client
Open a terminal in `Frontend/`:
```powershell
cd C:\Users\adina\Desktop\Infosys\document-agent\Frontend
npm run dev
```
- **Healthy Log Output:**
  ```text
  VITE v7.3.7  ready in 240 ms
  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.x.x:5173/
  ```

---

## 4. Database Migrations & Verification

To execute pending schema migrations against Supabase PostgreSQL:
```powershell
cd C:\Users\adina\Desktop\Infosys\document-agent\Engine
.\venv\Scripts\alembic.exe upgrade head
```

To run complete automated test verification:
```powershell
cd C:\Users\adina\Desktop\Infosys\document-agent\Engine
.\venv\Scripts\python.exe -m unittest discover tests -p "test_*.py" -v
```

To run the seed document pipeline verification script:
```powershell
cd C:\Users\adina\Desktop\Infosys\document-agent\Engine
.\venv\Scripts\python.exe scripts/verify_milestone2_pipeline.py
```

---

## 5. Troubleshooting Matrix

| Symptom | Probable Cause | Corrective Action |
| :--- | :--- | :--- |
| `GET /api/workspaces/... 500` | PostgreSQL returns raw `datetime` objects | Ensure `_format_row()` serializes to ISO strings in `repository.py` and schemas accept `Union[str, datetime]`. |
| `ChromaVectorStore has no attribute count` | Method name discrepancy | Use `vector_store.count_chunks()` or `vector_store.collection.count()`. |
| `AssertionError: 0 not >= 1` in search | Document hash exists in DB, but vector store lacks chunks | `service.py` checks `self.vector_store.get_chunks_by_document(doc_id)`. If empty, re-indexes automatically. |
| `psycopg.errors.AmbiguousParameter` | Reusing `:status` parameter across different SQL types | Differentiate parameters (e.g. `:status` for text and `:is_finished` for boolean conditions). |
| `Alembic ConfigParser %% error` | Unescaped `%` in database URL password | In `migrations/env.py`, use `db_url.replace("%", "%%")` when setting `sqlalchemy.url`. |

