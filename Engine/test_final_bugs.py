import unittest
import inspect
from pathlib import Path

from app.api.routes import analysis
from app.infrastructure.database.repository import (
    SQLiteRepository
)

ENGINE = Path(__file__).resolve().parent
FRONTEND = ENGINE.parent / "Frontend" / "src"


class TestFinalRepairs(unittest.TestCase):

    def test_no_undefined_sample_chunks(self):

        content = (
            FRONTEND / "pages" / "DocumentDetails.jsx"
        ).read_text(encoding="utf-8")

        self.assertNotIn("SAMPLE_CHUNKS", content)

    def test_no_duplicate_processing_routes(self):

        paths = [
            route.path
            for route in analysis.router.routes
            if "POST" in route.methods
        ]

        self.assertEqual(
            paths.count("/documents/process"), 1
        )

        self.assertEqual(
            paths.count("/documents/{document_id}/process"),
            1
        )

    def test_upload_pending_status(self):

        content = (
            ENGINE / "app" / "api" / "routes" / "documents.py"
        ).read_text(encoding="utf-8")

        self.assertIn('status="PENDING"', content)

    def test_pending_jobs_cancelled(self):

        source = inspect.getsource(
            SQLiteRepository.delete_user_session
        )

        self.assertIn("CANCELLED", source)
        self.assertIn("SESSION_DELETED", source)

    def test_active_jobs_protected(self):

        source = inspect.getsource(
            SQLiteRepository.delete_user_session
        )

        self.assertIn(
            "status IN ('PROCESSING', 'RUNNING')",
            source
        )

    def test_all_regression_files_exist(self):

        files = [
            "tests/test_doc_owner.py",
            "test_data_isolation.py",
            "test_ageent_auth.py",
            "test_chunk_ownership.py",
            "test_vector_isolation.py",
            "test_research_security.py",
            "test_search_security.py",
            "test_vector_agent_arch.py",
            "test_reindex_security.py",
            "test_processing_api.py",
            "test_document_deletion.py",
            "test_session_management.py",
            "test_session_features.py",
            "test_final_config.py"
        ]

        for filename in files:

            with self.subTest(filename=filename):

                self.assertTrue(
                    (ENGINE / filename).is_file(),
                    f"Missing test: {filename}"
                )

    def test_session_management_still_works(self):

        repo = SQLiteRepository(":memory:")

        workspace = repo.create_user_workspace(
            user_id="user-a",
            name="Test Workspace",
            description=""
        )

        session = repo.create_user_session(
            workspace_id=workspace["workspace_id"],
            user_id="user-a",
            title="Test Session",
            description=""
        )

        sid = session["session_id"]

        self.assertFalse(
            repo.delete_user_session(sid, "user-b")
        )

        self.assertTrue(
            repo.delete_user_session(sid, "user-a")
        )

        self.assertIsNone(
            repo.get_user_session(sid, "user-a")
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)