import unittest
from unittest.mock import Mock, patch
from pathlib import Path

from app.orchestration import automatic_processing as worker


ENGINE = Path(__file__).resolve().parent


class TestAutomaticProcessing(unittest.TestCase):

    def setUp(self):
        self.repo = Mock()

        self.document = {
            "document_id": "doc-a",
            "filename": "annual_report.pdf",
            "workspace_id": "workspace-a",
        }

        self.job = {
            "job_id": "job-a",
            "document_id": "doc-a",
            "workspace_id": "workspace-a",
            "session_id": "session-a",
            "status": "QUEUED",
        }

        self.repo.get_user_document.return_value = self.document
        self.repo.get_processing_job.return_value = self.job

        repo_patch = patch.object(
            worker,
            "get_database_repository",
            return_value=self.repo,
        )

        pipeline_patch = patch.object(
            worker.MultiAgentWorkflowOrchestrator,
            "run_pipeline",
        )

        repo_patch.start()
        self.pipeline = pipeline_patch.start()

        self.addCleanup(repo_patch.stop)
        self.addCleanup(pipeline_patch.stop)

    def process(self):
        return worker.process_uploaded_document(
            document_id="doc-a",
            user_id="user-a",
            workspace_id="workspace-a",
            session_id="session-a",
            job_id="job-a",
        )

    def test_automatic_pipeline(self):
        self.process()
        self.pipeline.assert_called_once()

    def test_authenticated_user(self):
        self.process()

        self.pipeline.assert_called_once_with(
            document_id="doc-a",
            filename="annual_report.pdf",
            workspace_id="workspace-a",
            session_id="session-a",
            user_id="user-a",
            job_id="job-a",
        )

    def test_unauthorized_document(self):
        self.repo.get_user_document.return_value = None

        self.process()

        self.pipeline.assert_not_called()
        self.repo.update_processing_job.assert_not_called()

    def test_workspace_mismatch(self):
        self.document["workspace_id"] = "foreign-workspace"

        self.process()

        self.pipeline.assert_not_called()

    def test_job_document_mismatch(self):
        self.job["document_id"] = "foreign-document"

        self.process()

        self.pipeline.assert_not_called()
        self.repo.update_processing_job.assert_not_called()

    def test_job_session_mismatch(self):
        self.job["session_id"] = "foreign-session"

        self.process()

        self.pipeline.assert_not_called()

    def test_missing_job(self):
        self.repo.get_processing_job.return_value = None

        self.process()

        self.pipeline.assert_not_called()

    def test_cancelled_job(self):
        self.job["status"] = "CANCELLED"

        self.process()

        self.pipeline.assert_not_called()

    def test_completed_job(self):
        self.job["status"] = "COMPLETED"

        self.process()

        self.pipeline.assert_not_called()

    def test_failed_pipeline(self):
        self.pipeline.side_effect = RuntimeError(
            "Processing failed"
        )

        self.process()

        self.repo.update_processing_job.assert_called_once_with(
            job_id="job-a",
            status="FAILED",
            current_stage="FAILED",
        )

    def test_upload_integration(self):
        content = (
            ENGINE / "app/api/routes/documents.py"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "background_tasks.add_task(",
            content,
        )

        self.assertIn(
            'status="QUEUED"',
            content,
        )

        self.assertIn(
            "process_uploaded_document",
            content,
        )

    def test_seed_integration(self):
        content = (
            ENGINE / "app/api/routes/documents.py"
        ).read_text(encoding="utf-8")

        seed_code = content.split(
            "def ingest_seed_documents(", 1
        )[1].split(
            "@router.get", 1
        )[0]

        self.assertIn(
            "background_tasks.add_task(",
            seed_code,
        )

    def test_session_upload_integration(self):
        content = (
            ENGINE / "app/api/routes/documents.py"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "background_tasks=background_tasks",
            content,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)