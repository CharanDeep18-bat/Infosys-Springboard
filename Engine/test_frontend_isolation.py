import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import health

ENGINE = Path(__file__).resolve().parent
FRONTEND = ENGINE.parent / "Frontend" / "src"


class TestFrontendIsolation(unittest.TestCase):

    def read(self, filename):
        return (FRONTEND / filename).read_text(
            encoding="utf-8"
        )

    def test_report_storage_disabled(self):
        content = self.read("data/reportData.js")
        self.assertNotIn("localStorage.getItem(", content)
        self.assertNotIn("localStorage.setItem(", content)

    def test_knowledge_storage_disabled(self):
        content = self.read("data/knowledgeBaseData.js")
        self.assertNotIn("localStorage.getItem(", content)
        self.assertNotIn("localStorage.setItem(", content)

    def test_orchestration_storage_disabled(self):
        content = self.read("data/orchestrationData.js")
        self.assertNotIn("localStorage.getItem(", content)
        self.assertNotIn("localStorage.setItem(", content)

    def test_chat_storage_disabled(self):
        content = self.read("data/researchChatData.js")
        self.assertNotIn("localStorage.getItem(", content)
        self.assertNotIn("localStorage.setItem(", content)

    def test_legacy_cache_cleanup(self):
        content = self.read("context/AuthContext.jsx")

        keys = [
            "finresearch_reports_v6",
            "finresearch_kb_records_v3",
            "finresearch_orchestration_state_v4",
            "finresearch_chat_history_v5_"
        ]

        for key in keys:
            self.assertIn(key, content)

        self.assertNotIn("localStorage.clear()", content)

    def test_report_documents(self):
        content = self.read(
            "components/report/ReportConfigModal.jsx"
        )

        self.assertNotIn("INITIAL_DOCUMENTS", content)
        self.assertIn("api.listDocuments()", content)
        self.assertIn("documentIds:", content)

    def test_no_default_fake_report(self):
        content = self.read("pages/ReportView.jsx")
        self.assertNotIn("INITIAL_REPORTS[0]", content)

    def test_no_fabricated_report_preview(self):
        content = self.read(
            "components/report/ReportPreview.jsx"
        )

        self.assertNotIn(
            "|| generateStructuredReportContent(report)",
            content
        )

    def test_public_health_information(self):
        app = FastAPI()
        app.include_router(health.router)

        with patch.object(
            health,
            "_internal_health_check",
            return_value={
                "status": "healthy",
                "database": {"provider": "SQLite"},
                "vector_store": {
                    "total_indexed_chunks": 500
                },
                "storage": {"path": "private"}
            }
        ):
            response = TestClient(app).get("/health")

            self.assertEqual(response.status_code, 200)

            self.assertEqual(
                response.json(),
                {"status": "healthy"}
            )

    def test_health_failure(self):
        app = FastAPI()
        app.include_router(health.router)

        with patch.object(
            health,
            "_internal_health_check",
            side_effect=RuntimeError("Private error")
        ):
            response = TestClient(app).get("/health")

            self.assertEqual(
                response.json(),
                {"status": "degraded"}
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)