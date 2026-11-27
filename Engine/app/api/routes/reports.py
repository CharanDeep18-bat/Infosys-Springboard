from typing import List
from fastapi.responses import Response

from app.agents.report_agent.pdf_exporter import (
    ReportPDFExporter,
)
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.agents.report_agent import ReportAgentService
from app.schemas.research import GeneratedReport

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.ownership import (
    require_owned_documents,
)
from app.agents.report_agent.report_repository import (
    ReportRepository,
)
router = APIRouter(tags=["Report Agent"])


class GenerateReportRequest(BaseModel):

    document_id: str

    comparison_document_ids: List[str] = Field(
        default_factory=list,
        max_length=10,
    )


@router.post(
    "/reports/generate",
    response_model=GeneratedReport
)
def generate_report(
    payload: GenerateReportRequest,
    user: dict = Depends(get_current_user)
):

    document_ids = list(dict.fromkeys(
        [payload.document_id]
        + payload.comparison_document_ids
    ))

    documents = require_owned_documents(
        document_ids=document_ids,
        user_id=user["id"],
    )

    workspace_id = documents[0]["workspace_id"]

    if any(
        d["workspace_id"] != workspace_id
        for d in documents
    ):
        raise HTTPException(
            status_code=400,
            detail="Documents must belong to the same workspace"
        )

    try:

        service = ReportAgentService()

        report = service.generate_report(
            document_id=payload.document_id,
            user_id=user["id"],
            comparison_document_ids=(
                payload.comparison_document_ids
            ),
        )

        return ReportRepository().save_report(
            user_id=user["id"],
            report=report,
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

@router.post("/reports/export/pdf")
def export_report_pdf(
    payload: GenerateReportRequest,
    user: dict = Depends(get_current_user),
):

    require_owned_documents(
        document_ids=list(dict.fromkeys(
            [payload.document_id]
            + payload.comparison_document_ids
        )),
        user_id=user["id"]
    )

    report = ReportAgentService().generate_report(
        document_id=payload.document_id,
        user_id=user["id"],
        comparison_document_ids=(
            payload.comparison_document_ids
        )
    )
    try:

        exporter = ReportPDFExporter()

        pdf_bytes = exporter.generate(report)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    'attachment; filename="financial-report.pdf"'
                ),
                "Cache-Control": "private, no-store",
            },
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail="PDF report generation failed",
        ) from exc


class RenameReportRequest(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200
    )


def require_owned_report(report_id, user_id):
    report = ReportRepository().get_report(
        report_id=report_id,
        user_id=user_id,
    )

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    return report


@router.get(
    "/reports",
    response_model=List[GeneratedReport]
)
def list_saved_reports(
    user: dict = Depends(get_current_user),
):
    return ReportRepository().list_reports(
        user_id=user["id"]
    )


@router.get(
    "/reports/{report_id}",
    response_model=GeneratedReport
)
def get_saved_report(
    report_id: str,
    user: dict = Depends(get_current_user),
):
    return require_owned_report(
        report_id,
        user["id"]
    )


@router.patch(
    "/reports/{report_id}",
    response_model=GeneratedReport
)
def rename_saved_report(
    report_id: str,
    payload: RenameReportRequest,
    user: dict = Depends(get_current_user),
):
    title = payload.title.strip()

    if not title:
        raise HTTPException(
            status_code=400,
            detail="Report title cannot be empty"
        )

    report = ReportRepository().rename_report(
        report_id=report_id,
        user_id=user["id"],
        title=title
    )

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    return report


@router.delete("/reports/{report_id}")
def delete_saved_report(
    report_id: str,
    user: dict = Depends(get_current_user),
):
    deleted = ReportRepository().delete_report(
        report_id=report_id,
        user_id=user["id"]
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    return {"deleted": True}


@router.get("/reports/{report_id}/pdf")
def download_saved_report(
    report_id: str,
    user: dict = Depends(get_current_user),
):
    report = require_owned_report(
        report_id,
        user["id"]
    )

    try:
        pdf_bytes = ReportPDFExporter().generate(report)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    'attachment; filename="financial-report.pdf"'
                ),
                "Cache-Control": "private, no-store"
            }
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="PDF export failed"
        ) from exc