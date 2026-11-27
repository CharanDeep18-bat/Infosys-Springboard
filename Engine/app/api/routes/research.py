from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends

from app.agents.research_agent import ResearchAgentService

from app.api.dependencies.auth import get_current_user

from app.api.dependencies.ownership import (
    require_owned_session,
    require_owned_documents,
    require_session_documents,
    get_owned_session
)

from app.infrastructure.database import (
    get_database_repository
)

from app.schemas.research import (
    ResearchAnswerResponse,
    ResearchMessageResponse,
    ResearchQueryRequest
)

router = APIRouter(tags=["Research Agent"])


def _run_query(
    session_id: Optional[str],
    payload: ResearchQueryRequest,
    user_id: str
) -> ResearchAnswerResponse:

    document_ids = payload.document_ids

    if session_id:

        session = require_owned_session(
            session_id, user_id
        )

        if document_ids is None:
            document_ids = session.get("document_ids") or []

        documents = require_session_documents(
            session_id,
            document_ids,
            user_id
        )

    else:

        if document_ids is None:

            repo = get_database_repository()

            document_ids = [
                d["document_id"]
                for d in repo.list_user_documents(
                    user_id=user_id
                )
                if d.get("indexed")
            ]

        documents = require_owned_documents(
            document_ids,
            user_id
        )

    document_ids = [
        d["document_id"]
        for d in documents
        if d.get("indexed")
    ]

    if not document_ids:
        raise HTTPException(
            status_code=400,
            detail="No indexed documents available for research."
        )

    try:

        service = ResearchAgentService()

        return service.answer_question(
            question=payload.question,
            document_ids=document_ids,
            session_id=session_id,
            top_k=payload.top_k,
            user_id=user_id
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Research Agent failed."
        ) from exc


@router.post(
    "/research/sessions/{session_id}/query",
    response_model=ResearchAnswerResponse
)
def query_research_session(
    session_id: str,
    payload: ResearchQueryRequest,
    user: dict = Depends(get_current_user)
):
    return _run_query(
        session_id,
        payload,
        user["id"]
    )


@router.post(
    "/research/query",
    response_model=ResearchAnswerResponse
)
def query_research(
    payload: ResearchQueryRequest,
    user: dict = Depends(get_current_user)
):
    return _run_query(
        None,
        payload,
        user["id"]
    )


@router.get(
    "/research/sessions/{session_id}/messages",
    response_model=List[ResearchMessageResponse]
)
def list_research_messages(
    session_id: str,
    session: dict = Depends(get_owned_session)
):
    service = ResearchAgentService()

    return service.get_history(
        session["session_id"]
    )


@router.delete(
    "/research/sessions/{session_id}/messages"
)
def clear_research_messages(
    session_id: str,
    session: dict = Depends(get_owned_session)
):
    service = ResearchAgentService()

    deleted = service.clear_history(
        session["session_id"]
    )

    return {
        "session_id": session["session_id"],
        "deleted": deleted
    }