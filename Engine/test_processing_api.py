import unittest

from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.routes import analysis
from app.api.dependencies.auth import get_current_user


class TestProcessingAPI(unittest.TestCase):

    def setUp(self):

        self.app = FastAPI()
        self.app.include_router(analysis.router)

        self.app.dependency_overrides[get_current_user] = (
            lambda: {"id": "user-a"}
        )

        self.client = TestClient(self.app)

        self.document = {
            "document_id": "doc-a",
            "filename": "report.pdf",
            "workspace_id": "workspace-a",
            "user_id": "user-a"
        }

        def owned_document(doc_id, user_id):
            if doc_id == "doc-a" and user_id == "user-a":
                return self.document

            raise HTTPException(
                status_code=404,
                detail="Document not found."
            )

        def owned_session_documents(session_id, ids, user_id):
            if (
                session_id == "session-a"
                and ids == ["doc-a"]
                and user_id == "user-a"
            ):
                return [self.document]

            raise HTTPException(
                status_code=404,
                detail="Session not found."
            )

        document_patch = patch.object(
            analysis,
            "require_owned_document",
            side_effect=owned_document
        )

        session_patch = patch.object(
            analysis,
            "require_session_documents",
            side_effect=owned_session_documents
        )

        workflow_patch = patch.object(
            analysis.MultiAgentWorkflowOrchestrator,
            "run_pipeline"
        )

        self.document_mock = document_patch.start()
        self.session_mock = session_patch.start()
        self.workflow = workflow_patch.start()

        self.addCleanup(document_patch.stop)
        self.addCleanup(session_patch.stop)
        self.addCleanup(workflow_patch.stop)

        self.workflow.return_value = SimpleNamespace(
            job_id="job-a",
            document_id="doc-a",
            current_phase="COMPLETED",
            total_pages=5,
            chunk_count=10,
            extracted_metrics_count=4,
            red_flag_count=2,
            errors=[],
            execution_steps=[]
        )

    def process(self, doc="doc-a", **kwargs):

        return self.client.post(
            f"/documents/{doc}/process",
            json={
                "document_id": doc,
                **kwargs
            }
        )

    def test_owned_processing(self):

        response = self.process()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["status"],
            "COMPLETED"
        )

    def test_cross_user_document(self):

        response = self.process("doc-b")

        self.assertEqual(response.status_code, 404)
        self.workflow.assert_not_called()

    def test_unauthenticated_processing(self):

        def unauthorized():
            raise HTTPException(status_code=401)

        self.app.dependency_overrides[get_current_user] = (
            unauthorized
        )

        self.assertEqual(
            self.process().status_code, 401
        )

        self.workflow.assert_not_called()

    def test_document_id_mismatch(self):

        response = self.client.post(
            "/documents/doc-a/process",
            json={"document_id": "doc-b"}
        )

        self.assertEqual(response.status_code, 400)
        self.workflow.assert_not_called()

    def test_owned_session(self):

        response = self.process(
            session_id="session-a"
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            self.workflow.call_args.kwargs["session_id"],
            "session-a"
        )

    def test_cross_user_session(self):

        response = self.process(
            session_id="session-b"
        )

        self.assertEqual(response.status_code, 404)
        self.workflow.assert_not_called()

    def test_trusted_identity(self):

        response = self.process(
            user_id="user-b",
            workspace_id="workspace-b",
            filename="malicious.pdf",
            storage_path="unauthorized.pdf"
        )

        self.assertEqual(response.status_code, 200)

        args = self.workflow.call_args.kwargs

        self.assertEqual(args["user_id"], "user-a")
        self.assertEqual(
            args["workspace_id"], "workspace-a"
        )
        self.assertEqual(args["filename"], "report.pdf")
        self.assertNotIn("storage_path", args)

    def test_failed_pipeline(self):

        self.workflow.return_value.current_phase = "FAILED"

        response = self.process()

        self.assertEqual(
            response.json()["status"], "FAILED"
        )

    def test_workflow_exception(self):

        self.workflow.side_effect = RuntimeError(
            "Internal sensitive information"
        )

        response = self.process()

        self.assertEqual(response.status_code, 500)

        self.assertNotIn(
            "Internal sensitive information",
            response.text
        )

    def test_legacy_processing_endpoint(self):

        response = self.client.post(
            "/documents/process",
            json={"document_id": "doc-a"}
        )

        self.assertEqual(response.status_code, 200)

    def test_path_only_processing(self):

        response = self.client.post(
            "/documents/doc-a/process"
        )

        self.assertEqual(response.status_code, 200)

    def test_missing_document_id(self):

        response = self.client.post(
            "/documents/process"
        )

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main(verbosity=2)