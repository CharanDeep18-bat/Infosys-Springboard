"""API route for the Report Agent."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.agents.report_agent import ReportAgentService
from app.schemas.research import GeneratedReport

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.ownership import require_owned_document

router = APIRouter(tags=["Report Agent"])


class GenerateReportRequest(BaseModel):
    document_id: str = Field(
        ...,
        description="Document to compile the report for"
    )


@router.post("/reports/generate", response_model=GeneratedReport)
def generate_report(
    payload: GenerateReportRequest,
    user: dict = Depends(get_current_user)
):
    document = require_owned_document(
        document_id=payload.document_id,
        user_id=user["id"]
    )

    try:
        service = ReportAgentService()

        return service.generate_report(
            document["document_id"]
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Report Agent failed"
        ) from exc