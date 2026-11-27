import unittest
import tempfile
import subprocess
import shutil

from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.infrastructure.database import SQLiteRepository
from app.agents.report_agent.report_repository import ReportRepository
from app.schemas.research import GeneratedReport, ReportSection
from app.api.routes import reports


ENGINE = Path(__file__).resolve().parent
FRONTEND = ENGINE.parent / "Frontend"
SRC = FRONTEND / "src"


class TestLiveIntegration(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()

        self.db_path = str(
            Path(self.temp.name) / "test.db"
        )

        self.db = SQLiteRepository(
            db_path=self.db_path
        )

        self.repo = ReportRepository(
            repository=self.db
        )

        self.report = GeneratedReport(
            report_id="report-a",
            document_id="doc-a",
            company_name="Test Company",
            fiscal_year=2025,
            title="Financial Research Report",
            generated_at="2026-01-01T10:00:00Z",
            status="COMPLETE",
            sections=[
                ReportSection(
                    section_key="executive_summary",
                    title="Executive Summary",
                    content_markdown="Test financial report"
                )
            ]
        )

        self.repo.save_report(
            "user-a",
            self.report
        )

        self.user_id = "user-a"

        app = FastAPI()
        app.include_router(reports.router)

        app.dependency_overrides[
            reports.get_current_user
        ] = lambda: {"id": self.user_id}

        self.client = TestClient(app)

        self.patcher = patch.object(
            reports,
            "ReportRepository",
            return_value=self.repo
        )

        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.client.close()
        self.temp.cleanup()

    def read_source(self, filename):
        return (SRC / filename).read_text(
            encoding="utf-8"
        )

    def test_report_saved(self):
        report = self.repo.get_report(
            "report-a", "user-a"
        )

        self.assertIsNotNone(report)
        self.assertEqual(
            report.title,
            self.report.title
        )

    def test_report_persistence(self):
        reopened = ReportRepository(
            repository=SQLiteRepository(
                db_path=self.db_path
            )
        )

        report = reopened.get_report(
            "report-a", "user-a"
        )

        self.assertIsNotNone(report)

    def test_owner_report_list(self):
        result = self.client.get("/reports")

        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.json()), 1)

    def test_foreign_report_list(self):
        self.user_id = "user-b"

        result = self.client.get("/reports")

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json(), [])

    def test_owner_report_access(self):
        result = self.client.get(
            "/reports/report-a"
        )

        self.assertEqual(result.status_code, 200)

    def test_foreign_report_access(self):
        self.user_id = "user-b"

        result = self.client.get(
            "/reports/report-a"
        )

        self.assertEqual(result.status_code, 404)

    def test_owner_report_rename(self):
        result = self.client.patch(
            "/reports/report-a",
            json={"title": "Updated Report"}
        )

        self.assertEqual(result.status_code, 200)

        saved = self.repo.get_report(
            "report-a", "user-a"
        )

        self.assertEqual(
            saved.title,
            "Updated Report"
        )

    def test_foreign_report_rename(self):
        self.user_id = "user-b"

        result = self.client.patch(
            "/reports/report-a",
            json={"title": "Unauthorized Update"}
        )

        self.assertEqual(result.status_code, 404)

        saved = self.repo.get_report(
            "report-a", "user-a"
        )

        self.assertEqual(
            saved.title,
            self.report.title
        )

    def test_empty_report_title(self):
        result = self.client.patch(
            "/reports/report-a",
            json={"title": "   "}
        )

        self.assertEqual(result.status_code, 400)

    def test_owner_report_delete(self):
        result = self.client.delete(
            "/reports/report-a"
        )

        self.assertEqual(result.status_code, 200)

        self.assertIsNone(
            self.repo.get_report(
                "report-a", "user-a"
            )
        )

    def test_foreign_report_delete(self):
        self.user_id = "user-b"

        result = self.client.delete(
            "/reports/report-a"
        )

        self.assertEqual(result.status_code, 404)

        self.assertIsNotNone(
            self.repo.get_report(
                "report-a", "user-a"
            )
        )

    def test_owner_saved_pdf(self):
        result = self.client.get(
            "/reports/report-a/pdf"
        )

        self.assertEqual(result.status_code, 200)

        self.assertTrue(
            result.content.startswith(b"%PDF")
        )

        self.assertEqual(
            result.headers["cache-control"],
            "private, no-store"
        )

    def test_foreign_saved_pdf(self):
        self.user_id = "user-b"

        result = self.client.get(
            "/reports/report-a/pdf"
        )

        self.assertEqual(result.status_code, 404)

    def test_missing_authentication(self):
        def reject():
            raise HTTPException(
                status_code=401,
                detail="Unauthorized"
            )

        self.client.app.dependency_overrides[
            reports.get_current_user
        ] = reject

        result = self.client.get("/reports")

        self.assertEqual(result.status_code, 401)

    def test_latest_processing_job(self):
        self.assertTrue(
            callable(
                getattr(
                    self.db,
                    "get_latest_processing_job",
                    None
                )
            )
        )

        self.assertIsNone(
            self.db.get_latest_processing_job(
                "missing-document"
            )
        )

    def test_document_status_fields(self):
        from app.schemas.document import DocumentSummary

        fields = DocumentSummary.model_fields

        for field in [
            "processing_status",
            "processing_stage",
            "processing_job_id"
        ]:
            self.assertIn(field, fields)

    def test_frontend_status_mapping(self):
        source = self.read_source(
            "services/api.js"
        )

        for value in [
            "resolveDocumentStatus",
            "processing_status",
            "processing_stage",
            "processing_job_id",
            "Boolean(doc.indexed)"
        ]:
            self.assertIn(value, source)

    def test_seed_import_integration(self):
        source = self.read_source(
            "pages/DocumentLibrary.jsx"
        )

        self.assertIn(
            "api.seedDocuments()",
            source
        )

        self.assertIn("2024-25", source)

    def test_document_status_polling(self):
        source = self.read_source(
            "pages/DocumentLibrary.jsx"
        )

        self.assertIn(
            "refreshProcessingStatus",
            source
        )

        self.assertIn(
            "api.listDocuments()",
            source
        )

    def test_live_orchestration(self):
        source = self.read_source(
            "pages/OrchestrationView.jsx"
        )

        self.assertIn(
            "api.listDocuments()",
            source
        )

        self.assertIn(
            "processingStage",
            source
        )

        self.assertNotIn(
            "INITIAL_TIMELINE_EVENTS",
            source
        )

        self.assertNotIn(
            "Math.random()",
            source
        )

    def test_live_knowledge_base(self):
        source = self.read_source(
            "pages/KnowledgeBase.jsx"
        )

        self.assertIn(
            "api.listDocuments()",
            source
        )

        self.assertIn(
            "doc.indexed",
            source
        )

        self.assertNotIn(
            "INITIAL_INDEXING_RECORDS",
            source
        )

        self.assertNotIn(
            "Math.random()",
            source
        )

    def test_frontend_report_persistence(self):
        source = self.read_source(
            "pages/ReportView.jsx"
        )

        for method in [
            "api.listReports()",
            "api.generateReport(",
            "api.renameReport(",
            "api.deleteReport(",
            "api.downloadSavedReport("
        ]:
            self.assertIn(method, source)

        self.assertNotIn(
            "localStorage",
            source
        )

    def test_frontend_report_api(self):
        source = self.read_source(
            "services/api.js"
        )

        for method in [
            "async listReports(",
            "async getReport(",
            "async renameReport(",
            "async deleteReport(",
            "async downloadSavedReport("
        ]:
            self.assertIn(method, source)

    def test_frontend_build(self):
        npm = (
            shutil.which("npm.cmd")
            or shutil.which("npm")
        )

        self.assertIsNotNone(
            npm,
            "npm not installed"
        )

        result = subprocess.run(
            [npm, "run", "build"],
            cwd=str(FRONTEND),
            timeout=300
        )

        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)