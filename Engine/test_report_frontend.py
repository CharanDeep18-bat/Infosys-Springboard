import unittest
import subprocess
import os

from pathlib import Path

FRONTEND = Path(__file__).resolve().parent.parent / "Frontend"
SRC = FRONTEND / "src"


class TestReportFrontend(unittest.TestCase):

    def read(self, path):
        return (SRC / path).read_text(encoding="utf-8")

    def test_report_api(self):
        content = self.read("services/api.js")
        self.assertIn("/reports/generate", content)
        self.assertIn("comparison_document_ids", content)

    def test_pdf_api(self):
        content = self.read("services/api.js")
        self.assertIn("/reports/export/pdf", content)
        self.assertIn('responseType: "blob"', content)

    def test_live_generation(self):
        content = self.read("pages/ReportView.jsx")
        self.assertIn("await api.generateReport(", content)

    def test_live_pdf_download(self):
        content = self.read("pages/ReportView.jsx")
        self.assertIn("await api.exportReportPdf(", content)
        self.assertIn("URL.createObjectURL", content)
        self.assertIn("URL.revokeObjectURL", content)

    def test_no_simulated_generation(self):
        content = self.read("pages/ReportView.jsx")
        self.assertNotIn("generateStructuredReportContent", content)
        self.assertNotIn("generationProgress: 90", content)
        self.assertNotIn("Milestone 4 — Under Development", content)

    def test_real_document_selection(self):
        content = self.read(
            "components/report/ReportConfigModal.jsx"
        )
        self.assertIn("api.listDocuments()", content)
        self.assertNotIn("INITIAL_DOCUMENTS", content)
        self.assertNotIn("SEED_COMPANIES", content)

    def test_comparison_selection(self):
        content = self.read(
            "components/report/ReportConfigModal.jsx"
        )
        self.assertIn("comparisonDocumentIds", content)
        self.assertIn("primaryId", content)

    def test_real_report_preview(self):
        content = self.read(
            "components/report/ReportPreview.jsx"
        )
        self.assertIn("section.content_markdown", content)
        self.assertIn("content.sections", content)
        self.assertNotIn("generateStructuredReportContent", content)

    def test_source_citations(self):
        content = self.read(
            "components/report/ReportPreview.jsx"
        )
        self.assertIn("citation.exact_quote", content)
        self.assertIn("citation.page_number", content)
        self.assertIn("citation.document_name", content)

    def test_no_shared_report_storage(self):
        content = self.read("pages/ReportView.jsx")
        self.assertNotIn("localStorage", content)
        self.assertNotIn("saveStoredReports", content)

    def test_production_build(self):
        npm = "npm.cmd" if os.name == "nt" else "npm"

        result = subprocess.run(
            [npm, "run", "build"],
            cwd=FRONTEND,
            capture_output=True,
            text=True
        )

        self.assertEqual(
            result.returncode,
            0,
            result.stdout + "\n" + result.stderr
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)