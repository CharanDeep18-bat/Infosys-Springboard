"""API Route: Semantic Retrieval."""

from fastapi import APIRouter, HTTPException, Depends

from app.agents.document_agent import DocumentAgentService

from app.api.dependencies.auth import get_current_user

from app.api.dependencies.ownership import (
    require_owned_document,
    require_owned_session,
    require_session_documents
)

from app.schemas.search import SearchRequest, SearchResponse

router = APIRouter(tags=["Search & Retrieval"])


@router.post("/search", response_model=SearchResponse)
def semantic_search(
    request: SearchRequest,
    user: dict = Depends(get_current_user)
):

    user_id = user["id"]

    if request.document_id:
        require_owned_document(
            request.document_id, user_id
        )

    if request.session_id:
        require_owned_session(
            request.session_id, user_id
        )

    if request.document_id and request.session_id:
        require_session_documents(
            request.session_id,
            [request.document_id],
            user_id
        )

    try:

        service = DocumentAgentService()

        return service.search(
            query=request.query,
            top_k=request.top_k,
            document_id=request.document_id,
            session_id=request.session_id,
            filter_tables_only=request.filter_tables_only,
            user_id=user_id
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Semantic search failed."
        ) from exc