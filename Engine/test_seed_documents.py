import unittest
import hashlib
from pathlib import Path

import fitz

from app.agents.document_agent.service import DocumentAgentService


ENGINE = Path(__file__).resolve().parent
SEED_DIR = ENGINE / "seed_documents"
EXPECTED = {
    "infosys_annual_report_fy25.pdf": "infosys",
    "tcs_annual_report_fy25.pdf": "tata consultancy",
    "wipro_annual_report_fy25.pdf": "wipro",
    "hcltech_annual_report_fy25.pdf": "hcl",
}

class TestSeedDocuments(unittest.TestCase):

    def test_seed_directory(self):
        self.assertTrue(SEED_DIR.is_dir())

    def test_required_documents(self):
        for filename in EXPECTED:
            with self.subTest(filename=filename):
                self.assertTrue(
                    (SEED_DIR / filename).is_file()
                )

    def test_document_count(self):
        self.assertEqual(
            len(list(SEED_DIR.rglob("*.pdf"))),
            4
        )

    def test_valid_pdf_files(self):
        for filename in EXPECTED:
            with self.subTest(filename=filename):
                with fitz.open(SEED_DIR / filename) as doc:
                    self.assertGreater(doc.page_count, 0)
                    self.assertFalse(doc.needs_pass)

    def test_company_names(self):
        for filename, company in EXPECTED.items():
            with self.subTest(filename=filename):
                with fitz.open(SEED_DIR / filename) as doc:
                    text = " ".join(
                        doc[i].get_text()
                        for i in range(min(30, len(doc)))
                    ).lower()

                    self.assertIn(
                        "".join(company.split()),
                        "".join(text.split())
                    )

    def test_financial_year(self):
        for filename in EXPECTED:
            with self.subTest(filename=filename):
                with fitz.open(SEED_DIR / filename) as doc:
                    text = " ".join(
                        doc[i].get_text()
                        for i in range(min(30, len(doc)))
                    )

                    normalized = "".join(text.split()).lower()

                    self.assertRegex(
                        normalized,
                        r"2024[-–—/](?:2025|25)|fy2025|fy25"
                    )

    def test_financial_content(self):
        keywords = [
            "revenue",
            "profit",
            "assets",
            "liabilities",
            "cash flow",
        ]

        for filename in EXPECTED:
            with self.subTest(filename=filename):
                with fitz.open(SEED_DIR / filename) as doc:
                    text = " ".join(
                        page.get_text()
                        for page in doc
                    ).lower()

                    matches = sum(
                        keyword in text
                        for keyword in keywords
                    )

                    self.assertGreaterEqual(matches, 4)

    def test_unique_documents(self):
        hashes = [
            hashlib.sha256(
                (SEED_DIR / filename).read_bytes()
            ).hexdigest()
            for filename in EXPECTED
        ]

        self.assertEqual(
            len(hashes),
            len(set(hashes))
        )

    def test_upload_size_limit(self):
        service = DocumentAgentService()

        for filename in EXPECTED:
            with self.subTest(filename=filename):
                size = (SEED_DIR / filename).stat().st_size

                self.assertLessEqual(
                    size,
                    service.settings.max_file_size
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)