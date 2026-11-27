import unittest
from unittest.mock import Mock

from app.agents.report_agent.service import (
    ReportAgentService
)


class TestReportAgent(unittest.TestCase):

    def setUp(self):

        self.repo = Mock()

        self.document = {
            "document_id": "doc-a",
            "filename": "company.pdf",
            "workspace_id": "workspace-a",
            "metadata": {
                "company_name": "Test Company"
            },
        }

        self.metric = {
            "metric_name": "REVENUE",
            "numeric_value": 1000,
            "currency": "INR",
            "unit": "CRORES",
            "statement_type": "INCOME_STATEMENT",
            "fiscal_year": 2024,
            "citation": {
                "page_number": 10,
                "exact_quote": "Revenue 1000",
            },
        }

        self.repo.get_user_document.return_value = (
            self.document
        )

        self.repo.get_financial_metrics.return_value = [
            self.metric
        ]

        self.repo.get_red_flag_findings.return_value = []

        self.service = ReportAgentService(
            repository=self.repo
        )

    def generate(self, **kwargs):

        return self.service.generate_report(
            document_id="doc-a",
            user_id="user-a",
            **kwargs,
        )

    def test_five_sections(self):

        report = self.generate()

        self.assertEqual(
            [s.section_key for s in report.sections],
            [
                "executive_summary",
                "key_financials",
                "red_flags",
                "company_comparison",
                "outlook",
            ],
        )

    def test_report_citations(self):

        report = self.generate()

        self.assertTrue(report.citations)

        self.assertTrue(
            all(c.document_id == "doc-a"
                for c in report.citations)
        )

    def test_unauthorized_document(self):

        self.repo.get_user_document.return_value = None

        with self.assertRaises(ValueError):
            self.generate()

        self.repo.get_financial_metrics.assert_not_called()

    def test_unauthorized_comparison(self):

        self.repo.get_user_document.side_effect = [
            self.document,
            None,
        ]

        with self.assertRaises(ValueError):
            self.generate(
                comparison_document_ids=["doc-b"]
            )

        self.repo.get_financial_metrics.assert_not_called()

    def test_cross_workspace_comparison(self):

        other = {
            **self.document,
            "document_id": "doc-b",
            "workspace_id": "workspace-b",
        }

        self.repo.get_user_document.side_effect = [
            self.document,
            other,
        ]

        with self.assertRaises(ValueError):
            self.generate(
                comparison_document_ids=["doc-b"]
            )

    def test_missing_metrics(self):

        self.repo.get_financial_metrics.return_value = []

        with self.assertRaises(ValueError):
            self.generate()

    def test_uncited_metrics(self):

        self.repo.get_financial_metrics.return_value = [
            {**self.metric, "citation": {}}
        ]

        with self.assertRaises(ValueError):
            self.generate()

    def test_red_flag_section(self):

        self.repo.get_red_flag_findings.return_value = [
            {
                "title": "Debt risk",
                "severity": "HIGH",
                "description": "Debt increased.",
                "supporting_evidence": "Debt increased",
                "source_page": 15,
            }
        ]

        report = self.generate()

        section = next(
            s for s in report.sections
            if s.section_key == "red_flags"
        )

        self.assertEqual(section.status, "generated")
        self.assertEqual(
            section.citations[0].page_number, 15
        )

    def test_single_document_comparison(self):

        report = self.generate()

        section = next(
            s for s in report.sections
            if s.section_key == "company_comparison"
        )

        self.assertEqual(
            section.status, "unavailable"
        )

    def test_outlook_no_forecast(self):

        report = self.generate()

        section = next(
            s for s in report.sections
            if s.section_key == "outlook"
        )

        self.assertIn(
            "not forecasts",
            section.content_markdown
        )

        self.assertTrue(section.citations)

    def test_no_planned_sections(self):

        report = self.generate()

        self.assertEqual(report.planned_sections, [])

        self.assertEqual(
            report.status,
            "COMPLETE_WITH_LIMITATIONS"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)