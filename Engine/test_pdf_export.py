import unittest
from unittest.mock import patch

import fitz

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.schemas.research import (
    GeneratedReport,
    ReportSection,
    AgentCitation,
)

from app.agents.report_agent.pdf_exporter import (
    ReportPDFExporter,
)

from app.api.routes import reports


class TestPDFExport(unittest.TestCase):

    def setUp(self):

        self.citation = AgentCitation(
            document_id="doc-a",
            document_name="annual_report.pdf",
            page_number=10,
            exact_quote="Reported revenue was 1000.",
            metric_name="REVENUE",
        )

        self.report = GeneratedReport(
            report_id="report-a",
            document_id="doc-a",
            company_name="Test Company",
            fiscal_year=2024,
            title="Financial Research Report",
            generated_at="2026-01-01",
            status="COMPLETE_WITH_LIMITATIONS",
            sections=[
                ReportSection(
                    section_key="executive_summary",
                    title="Executive Summary",
                    content_markdown="Reported revenue was 1000.",
                    citations=[self.citation],
                ),
                ReportSection(
                    section_key="key_financials",
                    title="Key Financials",
                    content_markdown=(
                        "| Metric | Value |\n"
                        "| --- | --- |\n"
                        "| Revenue | 1000 |"
                    ),
                ),
                ReportSection(
                    section_key="red_flags",
                    title="Red Flags",
                    status="unavailable",
                    content_markdown="No verified findings.",
                ),
                ReportSection(
                    section_key="company_comparison",
                    title="Company Comparison",
                    status="unavailable",
                    content_markdown="Comparison unavailable.",
                ),
                ReportSection(
                    section_key="outlook",
                    title="Outlook",
                    content_markdown="Historical indicators only.",
                ),
            ],
            citations=[self.citation],
            limitations=[
                "Missing values are not estimated."
            ],
        )

        self.exporter = ReportPDFExporter()

        self.pdf = self.exporter.generate(self.report)

        with fitz.open(
            stream=self.pdf,
            filetype="pdf",
        ) as document:

            self.text = "\n".join(
                page.get_text()
                for page in document
            )

        app = FastAPI()
        app.include_router(reports.router)

        app.dependency_overrides[
            reports.get_current_user
        ] = lambda: {"id": "user-a"}

        self.client = TestClient(app)

    def test_valid_pdf(self):

        self.assertTrue(
            self.pdf.startswith(b"%PDF")
        )

    def test_company_name(self):

        self.assertIn(
            "Test Company", self.text
        )

    def test_all_five_sections(self):

        for title in [
            "Executive Summary",
            "Key Financials",
            "Red Flags",
            "Company Comparison",
            "Outlook",
        ]:

            self.assertIn(title, self.text)

    def test_financial_values(self):

        self.assertIn("Revenue", self.text)
        self.assertIn("1000", self.text)

    def test_source_citations(self):

        self.assertIn(
            "annual_report.pdf", self.text
        )

        self.assertIn("Page 10", self.text)

    def test_exact_evidence(self):

        self.assertIn(
            "Reported revenue was 1000.",
            self.text,
        )

    def test_limitations(self):

        self.assertIn(
            "Missing values are not estimated.",
            self.text,
        )

    def test_unavailable_section(self):

        self.assertIn(
            "Section status: unavailable",
            self.text,
        )

    def test_pdf_endpoint(self):

        with patch.object(
            reports,
            "require_owned_documents",
            return_value=[]
        ), patch.object(
            reports.ReportAgentService,
            "generate_report",
            return_value=self.report
        ):

            response = self.client.post(
                "/reports/export/pdf",
                json={"document_id": "doc-a"}
            )

        self.assertEqual(
            response.status_code, 200
        )

        self.assertEqual(
            response.headers["content-type"],
            "application/pdf"
        )

        self.assertTrue(
            response.content.startswith(b"%PDF")
        )

        self.assertEqual(
            response.headers["cache-control"],
            "private, no-store"
        )

    def test_unauthorized_document(self):

        with patch.object(
            reports,
            "require_owned_documents",
            side_effect=HTTPException(
                status_code=404,
                detail="Document not found",
            ),
        ):

            response = self.client.post(
                "/reports/export/pdf",
                json={"document_id": "foreign-doc"},
            )

        self.assertEqual(response.status_code, 404)

    def test_missing_authentication(self):

        def reject():

            raise HTTPException(
                status_code=401,
                detail="Unauthorized",
            )

        self.client.app.dependency_overrides[
            reports.get_current_user
        ] = reject

        response = self.client.post(
            "/reports/export/pdf",
            json={"document_id": "doc-a"},
        )

        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main(verbosity=2)