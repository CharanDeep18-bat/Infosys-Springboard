import unittest

from pathlib import Path
from unittest.mock import Mock, patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.config import get_settings
from app.api.routes import documents
from app.api.dependencies.auth import get_current_user


class TestFinalConfiguration(unittest.TestCase):

    def test_vector_configuration(self):

        settings = get_settings()

        self.assertEqual(
            settings.vector_store_type.lower(),
            "chroma"
        )

    def test_storage_configuration(self):

        settings = get_settings()

        self.assertEqual(
            settings.storage_provider.lower(),
            "local"
        )

    def test_seed_requires_authentication(self):

        app = FastAPI()
        app.include_router(documents.router)

        def unauthorized():
            raise HTTPException(status_code=401)

        app.dependency_overrides[get_current_user] = (
            unauthorized
        )

        client = TestClient(app)

        with patch.object(
            documents, "DocumentAgentService"
        ) as service:

            response = client.post("/documents/seed")

            self.assertEqual(response.status_code, 401)

            service.assert_not_called()

    def test_seed_missing_directory(self):

        app = FastAPI()
        app.include_router(documents.router)

        app.dependency_overrides[get_current_user] = (
            lambda: {"id": "user-a"}
        )

        service = Mock()

        service.settings.seed_docs_dir = str(
            Path.cwd() / "__nonexistent_seed_directory__"
        )

        repo = Mock()

        repo.get_or_create_default_workspace.return_value = {
            "workspace_id": "workspace-a"
        }

        with patch.object(
            documents,
            "DocumentAgentService",
            return_value=service
        ), patch.object(
            documents,
            "get_database_repository",
            return_value=repo
        ):

            response = TestClient(app).post(
                "/documents/seed"
            )

            self.assertEqual(response.status_code, 404)

            service.process_pdf_upload.assert_not_called()

            repo.get_or_create_default_workspace.assert_called_once_with(
                "user-a"
            )

    def test_no_sample_research_documents(self):

        frontend = (
            Path(__file__).resolve().parent.parent
            / "Frontend" / "src"
        )

        content = (
            frontend / "pages" / "ConversationalResearch.jsx"
        ).read_text(encoding="utf-8")

        self.assertNotIn("INITIAL_DOCUMENTS", content)
        self.assertNotIn("getStoredDocuments()", content)

    def test_no_fake_ocr_error(self):

        frontend = (
            Path(__file__).resolve().parent.parent
            / "Frontend" / "src"
        )

        content = (
            frontend / "pages" / "DocumentDetails.jsx"
        ).read_text(encoding="utf-8")

        self.assertNotIn(
            "OCR Parsing Error Detected on Page 42",
            content
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)