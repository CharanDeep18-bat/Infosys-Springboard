"""API route for the Comparison Agent."""

from fastapi import APIRouter, HTTPException, Depends

from app.agents.comparison_agent import ComparisonAgentService

from app.api.dependencies.auth import get_current_user

from app.api.dependencies.ownership import (
    require_owned_documents
)

from app.schemas.research import (
    ComparisonRequest,
    ComparisonResponse
)

router = APIRouter(tags=["Comparison Agent"])


@router.post(
    "/comparison",
    response_model=ComparisonResponse
)
def compare_companies(
    payload: ComparisonRequest,
    user: dict = Depends(get_current_user)
):
    documents = require_owned_documents(
        document_ids=payload.document_ids,
        user_id=user["id"]
    )

    document_ids = [
        doc["document_id"]
        for doc in documents
    ]

    if len(document_ids) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least two distinct documents are required"
        )

    try:
        service = ComparisonAgentService()

        return service.compare_documents(
            document_ids=document_ids,
            metrics=payload.metrics
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Comparison Agent failed"
        ) from exc