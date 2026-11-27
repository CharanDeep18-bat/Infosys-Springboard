"""API Route: Financial Metric Extraction."""

from fastapi import APIRouter, HTTPException, Depends

from app.agents.extraction_agent import ExtractionAgentService

from app.api.dependencies.ownership import get_owned_document

router = APIRouter(tags=["Extraction"])


@router.get("/documents/{document_id}/extraction")
def get_extracted_financials(
    document_id: str,
    document: dict = Depends(get_owned_document)
):
    service = ExtractionAgentService()

    results = service.get_extracted_financials(
        document["document_id"]
    )

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No extracted financial metrics found for this document."
        )

    return results