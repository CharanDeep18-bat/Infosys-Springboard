import logging
from threading import Lock

from app.infrastructure.database import get_database_repository
from app.orchestration.workflow import MultiAgentWorkflowOrchestrator

logger = logging.getLogger(__name__)

processing_lock = Lock()


def process_uploaded_document(
    document_id: str,
    user_id: str,
    workspace_id: str,
    session_id=None,
    job_id=None,
):
    repo = get_database_repository()

    with processing_lock:
        try:
            document = repo.get_user_document(
                document_id=document_id,
                user_id=user_id,
            )

            if not document:
                raise ValueError("Document not found.")

            if document["workspace_id"] != workspace_id:
                raise ValueError("Workspace mismatch.")

            if job_id:
                job = repo.get_processing_job(job_id)

                if not job:
                    return

                if (
                    job["document_id"] != document_id
                    or job["workspace_id"] != workspace_id
                    or job.get("session_id") != session_id
                ):
                    return

                if job["status"] != "QUEUED":
                    return

            return MultiAgentWorkflowOrchestrator.run_pipeline(
                document_id=document_id,
                filename=document["filename"],
                workspace_id=workspace_id,
                session_id=session_id,
                user_id=user_id,
                job_id=job_id,
            )

        except Exception:
            logger.exception(
                "Automatic document processing failed: %s",
                document_id,
            )

            if job_id:
                job = repo.get_processing_job(job_id)

                if (
                    job
                    and job["document_id"] == document_id
                    and job["workspace_id"] == workspace_id
                    and job.get("session_id") == session_id
                    and job["status"] in ("QUEUED", "PROCESSING")
                    and repo.get_user_document(
                        document_id=document_id,
                        user_id=user_id,
                    )
                ):
                    repo.update_processing_job(
                        job_id=job_id,
                        status="FAILED",
                        current_stage="FAILED",
                    )

            return None