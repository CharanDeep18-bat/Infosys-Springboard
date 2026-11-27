"""API Route: Health & System Diagnostics.

Verifies:
- Application status & version
- Database provider & connectivity
- Storage provider & local/Supabase availability
- Vector database provider (Qdrant / ChromaDB) & healthy chunk count
- Embedding provider & vector dimension
- LLM provider & reasoning configuration readiness
- Persistent worker queue state
"""

from fastapi import APIRouter
from app.config import get_settings
from app.infrastructure.database import get_database_repository
from app.infrastructure.document_processing.embedder import get_embedding_provider
from app.infrastructure.storage import get_file_storage
from app.infrastructure.vector_store import get_vector_store

router = APIRouter(tags=["Health"])


def _internal_health_check():
    """Comprehensive health check verifying DB, storage, vector store, embedding, and LLM readiness."""
    settings = get_settings()
    vector_store = get_vector_store()
    repo = get_database_repository()
    storage = get_file_storage()
    emb_engine = get_embedding_provider()

    vs_healthy = vector_store.is_healthy()
    chunk_count = vector_store.count_chunks() if vs_healthy else 0
    emb_dim = emb_engine.get_dimension()
    emb_model = emb_engine.get_model_name()

    # Query queued and running jobs
    queued_jobs = 0
    processing_jobs = 0
    db_healthy = False
    try:
        if hasattr(repo, "get_queue_stats"):
            stats = repo.get_queue_stats()
            queued_jobs = stats.get("queued_jobs", 0)
            processing_jobs = stats.get("processing_jobs", 0)
        elif hasattr(repo, "_get_connection"):
            with repo._get_connection() as conn:
                q_row = conn.execute("SELECT COUNT(*) as c FROM ai_processing_jobs WHERE status = 'QUEUED'").fetchone()
                p_row = conn.execute("SELECT COUNT(*) as c FROM ai_processing_jobs WHERE status = 'PROCESSING'").fetchone()
                queued_jobs = q_row["c"] if q_row else 0
                processing_jobs = p_row["c"] if p_row else 0
        db_healthy = repo.is_healthy() if hasattr(repo, "is_healthy") else True
    except Exception:
        db_healthy = False

    # Storage health check
    try:
        storage_health = storage.check_health()
        storage_healthy = bool(storage_health.get("healthy", False))
    except Exception as exc:
        storage_healthy = False
        storage_health = {
            "healthy": False,
            "provider": getattr(storage, "get_storage_provider", lambda: type(storage).__name__)(),
            "error": str(exc),
        }

    # LLM credential readiness check (without leaking secrets)
    has_openai_key = bool(settings.openai_api_key or settings.llm_api_key)
    llm_configured = True if (settings.llm_provider != "openai" or has_openai_key) else False

    is_overall_healthy = db_healthy and vs_healthy and storage_healthy

    return {
        "status": "healthy" if is_overall_healthy else "degraded",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "database": {
            "provider": type(repo).__name__,
            "connected": db_healthy,
        },
        "storage": storage_health,
        "vector_store": {
            "provider": type(vector_store).__name__,
            "healthy": vs_healthy,
            "collection": getattr(vector_store, "collection_name", "unknown"),
            "total_indexed_chunks": chunk_count,
        },
        "embedding_engine": {
            "provider": settings.embedding_provider,
            "model": emb_model,
            "dimension": emb_dim,
        },
        "llm_engine": {
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "reasoning_effort": settings.llm_reasoning_effort,
            "credentials_configured": llm_configured,
        },
        "worker_queue": {
            "queued_jobs": queued_jobs,
            "processing_jobs": processing_jobs,
            "poll_interval_seconds": settings.worker_poll_seconds,
        },
    }
@router.get("/health")
def health_check():
    try:
        result = _internal_health_check()

        return {
            "status": result["status"]
        }

    except Exception:
        return {
            "status": "degraded"
        }