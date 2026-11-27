"""API Routes: Risk Analysis, Workflow Orchestration & Job Status."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends
from app.api.dependencies.auth import get_current_user
from app.agents.red_flag_agent import RedFlagAgentService
from app.infrastructure.database import get_database_repository
from app.orchestration.workflow import MultiAgentWorkflowOrchestrator
from app.api.dependencies.ownership import (
    require_owned_document,
    require_session_documents,
    get_owned_document
)
router = APIRouter(tags=["Analysis & Orchestration"])


# class ProcessDocumentRequest(BaseModel):
#     document_id: str = Field(..., description="Unique document identifier")
#     filename: str = Field(..., description="Document file name")
#     workspace_id: Optional[str] = Field(default="default-workspace")
#     session_id: Optional[str] = Field(default=None)
#     user_id: Optional[str] = Field(default=None)
#     storage_path: Optional[str] = Field(default=None, description="Filesystem or storage bucket path")

class ProcessDocumentRequest(BaseModel):
    document_id: str = Field(
        ...,
        description="Unique document identifier"
    )

    session_id: Optional[str] = Field(default=None)
@router.post("/documents/process")
@router.post("/documents/{document_id}/process")
def process_document(
    request: Optional[ProcessDocumentRequest] = None,
    document_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):

    if document_id and request:
        if document_id != request.document_id:
            raise HTTPException(
                status_code=400,
                detail="Document ID mismatch."
            )

    doc_id = document_id or (
        request.document_id if request else None
    )

    if not doc_id:
        raise HTTPException(
            status_code=400,
            detail="Document ID is required."
        )

    user_id = user["id"]

    document = require_owned_document(
        doc_id, user_id
    )

    session_id = request.session_id if request else None

    if session_id:
        require_session_documents(
            session_id,
            [doc_id],
            user_id
        )

    try:

        final_state = MultiAgentWorkflowOrchestrator.run_pipeline(
            document_id=doc_id,
            filename=document["filename"],
            workspace_id=document["workspace_id"],
            session_id=session_id,
            user_id=user_id
        )

        return {
            "job_id": final_state.job_id,
            "document_id": final_state.document_id,
            "status": final_state.current_phase,
            "phase": final_state.current_phase,
            "pages": final_state.total_pages,
            "chunks": final_state.chunk_count,
            "metrics_extracted": final_state.extracted_metrics_count,
            "red_flags": final_state.red_flag_count,
            "errors": (
                ["Document processing failed."]
                if final_state.current_phase == "FAILED"
                else []
            ),
            "execution_steps": [
                {
                    "step_name": s.step_name,
                    "agent": s.agent,
                    "status": s.status,
                    "timestamp": s.timestamp
                }
                for s in final_state.execution_steps
            ]
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Unable to process document."
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Document processing failed."
        ) from exc
@router.get("/documents/{document_id}/status")
def get_document_status(
    document_id: str,
    user: dict = Depends(get_current_user)
):
    """Query ingestion and processing status for an AI document."""
    repo = get_database_repository()
    doc = repo.get_user_document(
        document_id=document_id,
        user_id=user["id"]
    )  
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found.")

    runs = repo.get_agent_runs(document_id)
    stages = {r["agent_name"]: r["status"] for r in runs}

    return {
        "document_id": document_id,
        "filename": doc.get("filename"),
        "total_pages": doc.get("total_pages", 0),
        "total_characters": doc.get("total_characters", 0),
        "chunk_count": doc.get("chunk_count", 0),
        "indexed": bool(doc.get("indexed", 0)),
        "created_at": doc.get("created_at"),
        "stages": stages or {"DOCUMENT_AGENT": "INDEXED" if doc.get("indexed") else "PENDING"},
    }

@router.get("/documents/{document_id}/red-flags")
def get_document_red_flags(
    document_id: str,
    document: dict = Depends(get_owned_document)
):
    service = RedFlagAgentService()

    findings = service.get_document_red_flags(
        document["document_id"]
    )

    return {
        "document_id": document["document_id"],
        "total_findings": len(findings),
        "findings": findings,
    }

@router.get("/workflows/{run_id}/status")
def get_workflow_run_status(
    run_id: str,
    user: dict = Depends(get_current_user)
):
    repo = get_database_repository()

    job = repo.get_processing_job(run_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Workflow job not found"
        )

    doc = repo.get_user_document(
        document_id=job["document_id"],
        user_id=user["id"]
    )

    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Workflow job not found"
        )

    return job