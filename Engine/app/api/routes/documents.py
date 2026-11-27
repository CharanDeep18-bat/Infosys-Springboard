"""API Routes: Document Upload, Registration, and Management."""

from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, Depends
from app.api.dependencies.auth import get_current_user
from fastapi.responses import FileResponse

from app.agents.document_agent import DocumentAgentService
from app.infrastructure.database import get_database_repository
from app.infrastructure.storage import get_file_storage
from app.schemas.document import DocumentSummary, DocumentUploadResponse, SeedDocumentResult
from app.infrastructure.vector_store import get_vector_store

from app.api.dependencies.ownership import (
    require_owned_document
)
router = APIRouter(tags=["Documents"])


def build_document_summary(d):
    created_val = d.get("created_at")

    if hasattr(created_val, "isoformat"):
        created_val = created_val.isoformat()
    elif created_val is not None:
        created_val = str(created_val)
    else:
        created_val = ""

    return DocumentSummary(
        document_id=d["document_id"],
        workspace_id=d.get("workspace_id"),
        filename=d["filename"],
        stored_filename=d["stored_filename"],
        sha256=d["sha256"],
        total_pages=d.get("total_pages", 0),
        total_characters=d.get("total_characters", 0),
        chunk_count=d.get("chunk_count", 0),
        indexed=bool(d.get("indexed", 0)),
        created_at=created_val,
        metadata=d.get("metadata", {})
    )


@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse
)
async def upload_document(
    file: UploadFile = File(...),
    workspace_id: Optional[str] = Query(default=None),
    session_id: Optional[str] = Query(default=None),
    user: dict = Depends(get_current_user),
):
    try:
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Filename cannot be empty"
            )

        repo = get_database_repository()
        user_id = user["id"]

        if session_id:
            session = repo.get_user_session(
                session_id=session_id,
                user_id=user_id
            )

            if not session:
                raise HTTPException(
                    status_code=404,
                    detail="Session not found"
                )

            if workspace_id and workspace_id != session["workspace_id"]:
                raise HTTPException(
                    status_code=404,
                    detail="Session not found in workspace"
                )

            workspace_id = session["workspace_id"]

        if not workspace_id:
            workspace = repo.get_or_create_default_workspace(
                user_id=user_id
            )
            workspace_id = workspace["workspace_id"]

        workspace = repo.get_user_workspace(
            workspace_id=workspace_id,
            user_id=user_id
        )

        if not workspace:
            raise HTTPException(
                status_code=404,
                detail="Workspace not found"
            )

        service = DocumentAgentService()

        content = await file.read(
            service.settings.max_file_size + 1
        )

        result = service.process_pdf_upload(
            file_bytes=content,
            filename=file.filename,
            workspace_id=workspace_id,
            session_id=session_id,
            user_id=user_id
        )

        if not result.already_exists:
            job = repo.create_processing_job(
                document_id=result.document_id,
                workspace_id=workspace_id,
                session_id=session_id,
                status="PENDING",
                current_stage="DOCUMENT_INGESTED",
            )

            result.job_id = job["job_id"]

        return result

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail="Document processing failed"
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to process document"
        ) from exc

    finally:
        await file.close()
@router.post(
    "/sessions/{session_id}/documents/upload",
    response_model=DocumentUploadResponse
)
async def upload_document_to_session(
    session_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    repo = get_database_repository()

    session = repo.get_user_session(
        session_id=session_id,
        user_id=user["id"]
    )

    if not session:
        await file.close()

        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    return await upload_document(
        file=file,
        workspace_id=session["workspace_id"],
        session_id=session_id,
        user=user
    )


@router.get("/documents/{document_id}", response_model=DocumentSummary)
def get_document(
    document_id: str,
    user: dict = Depends(get_current_user)
):
    repo = get_database_repository()

    doc = repo.get_user_document(
        document_id=document_id,
        user_id=user["id"]
    )

    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return build_document_summary(doc)

@router.get("/documents", response_model=List[DocumentSummary])
def list_documents(
    workspace_id: Optional[str] = Query(default=None),
    user: dict = Depends(get_current_user)
):
    repo = get_database_repository()

    if workspace_id:
        workspace = repo.get_user_workspace(
            workspace_id=workspace_id,
            user_id=user["id"]
        )

        if not workspace:
            raise HTTPException(
                status_code=404,
                detail="Workspace not found"
            )

    raw_docs = repo.list_user_documents(
        user_id=user["id"],
        workspace_id=workspace_id
    )

    return [
        build_document_summary(d)
        for d in raw_docs
    ]
@router.post("/documents/seed")
def ingest_seed_documents(
    user: dict = Depends(get_current_user)
):
    from pathlib import Path

    service = DocumentAgentService()
    repo = get_database_repository()

    user_id = user["id"]

    workspace = repo.get_or_create_default_workspace(
        user_id
    )

    workspace_id = workspace["workspace_id"]

    seed_dir = Path(service.settings.seed_docs_dir)

    if not seed_dir.is_dir():
        raise HTTPException(
            status_code=404,
            detail="Seed document directory not found."
        )

    results = []

    for pdf in sorted(seed_dir.rglob("*.pdf")):

        try:
            if pdf.stat().st_size > service.settings.max_file_size:
                raise ValueError("File size limit exceeded.")

            result = service.process_pdf_upload(
                file_bytes=pdf.read_bytes(),
                filename=pdf.name,
                workspace_id=workspace_id,
                user_id=user_id
            )

            results.append({
                "filename": pdf.name,
                "status": "success",
                "document_id": result.document_id
            })

        except Exception:
            results.append({
                "filename": pdf.name,
                "status": "failed"
            })

    return results
@router.get("/documents/{document_id}/file")
def download_document_file(
    document_id: str,
    user: dict = Depends(get_current_user)
):
    from fastapi import Response
    from urllib.parse import quote

    repo = get_database_repository()

    doc = repo.get_user_document(
        document_id=document_id,
        user_id=user["id"]
    )

    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    storage = get_file_storage()

    meta = doc.get("metadata") or {}

    object_key = (
        meta.get("object_key")
        or doc.get("stored_filename")
        or f"{document_id}.pdf"
    )

    try:
        file_bytes = storage.get_file_bytes(
            document_id,
            object_key=object_key
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="PDF file not found"
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve PDF"
        ) from exc

    filename = doc.get(
        "filename", f"{document_id}.pdf"
    )

    return Response(
        content=file_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f"inline; filename*=UTF-8''{quote(filename, safe='')}",
            "Cache-Control": "private, no-store"
        }
    )

@router.delete("/documents/{document_id}")
def delete_document(
    document_id: str,
    user: dict = Depends(get_current_user)
):

    user_id = user["id"]

    document = require_owned_document(
        document_id, user_id
    )

    repo = get_database_repository()
    storage = get_file_storage()
    vector = get_vector_store()

    if storage.get_storage_provider() != "local":
        raise HTTPException(
            status_code=503,
            detail="Storage deletion is not supported yet."
        )

    if getattr(vector, "collection", None) is None:
        raise HTTPException(
            status_code=503,
            detail="Native vector deletion is unavailable."
        )

    try:

        deleted = vector.delete_owned_chunks(
            document_id,
            user_id=user_id,
            workspace_id=document["workspace_id"]
        )

        if not deleted:
            raise RuntimeError("Vector deletion failed.")

        storage.delete_file(document_id)

        if storage.get_file_path(document_id):
            raise RuntimeError("PDF deletion failed.")

        if not repo.delete_user_document(
            document_id, user_id
        ):
            raise RuntimeError("Database deletion failed.")

        return {
            "status": "deleted",
            "document_id": document_id
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Document deletion could not be completed."
        ) from exc
@router.get(
    "/sessions/{session_id}/documents",
    response_model=List[DocumentSummary]
)
def list_session_documents(
    session_id: str,
    user: dict = Depends(get_current_user)
):
    repo = get_database_repository()

    session = repo.get_user_session(
        session_id=session_id,
        user_id=user["id"]
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    summaries = []

    for document_id in session.get("document_ids", []):
        doc = repo.get_user_document(
            document_id=document_id,
            user_id=user["id"]
        )

        if doc and doc["workspace_id"] == session["workspace_id"]:
            summaries.append(build_document_summary(doc))

    return summaries