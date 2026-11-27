import unittest

from unittest.mock import Mock, patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.routes import documents
from app.api.dependencies.auth import get_current_user


class TestDocumentDeletion(unittest.TestCase):

    def setUp(self):

        app = FastAPI()
        app.include_router(documents.router)

        app.dependency_overrides[get_current_user] = (
            lambda: {"id": "user-a"}
        )

        self.app = app
        self.client = TestClient(app)

        self.repo = Mock()
        self.storage = Mock()
        self.vector = Mock()

        self.storage.get_storage_provider.return_value = "local"
        self.storage.get_file_path.return_value = None
        self.vector.delete_owned_chunks.return_value = True
        self.repo.delete_user_document.return_value = True

        def owned_document(doc_id, user_id):

            if doc_id == "doc-a" and user_id == "user-a":
                return {
                    "document_id": "doc-a",
                    "user_id": "user-a",
                    "workspace_id": "workspace-a"
                }

            raise HTTPException(status_code=404)

        patches = {
            "require_owned_document": Mock(
                side_effect=owned_document
            ),
            "get_database_repository": Mock(
                return_value=self.repo
            ),
            "get_file_storage": Mock(
                return_value=self.storage
            ),
            "get_vector_store": Mock(
                return_value=self.vector
            )
        }

        for name, replacement in patches.items():

            p = patch.object(
                documents, name, replacement
            )

            p.start()
            self.addCleanup(p.stop)

    def delete(self, doc="doc-a"):
        return self.client.delete(
            f"/documents/{doc}"
        )

    def test_owned_deletion(self):

        response = self.delete()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["status"], "deleted"
        )

    def test_cross_user_deletion(self):

        self.assertEqual(
            self.delete("doc-b").status_code, 404
        )

        self.vector.delete_owned_chunks.assert_not_called()
        self.storage.delete_file.assert_not_called()
        self.repo.delete_user_document.assert_not_called()

    def test_unauthenticated(self):

        def unauthorized():
            raise HTTPException(status_code=401)

        self.app.dependency_overrides[get_current_user] = (
            unauthorized
        )

        self.assertEqual(
            self.delete().status_code, 401
        )

    def test_vector_scope(self):

        self.delete()

        self.vector.delete_owned_chunks.assert_called_once_with(
            "doc-a",
            user_id="user-a",
            workspace_id="workspace-a"
        )

    def test_storage_deletion(self):

        self.delete()

        self.storage.delete_file.assert_called_once_with(
            "doc-a"
        )

    def test_database_scope(self):

        self.delete()

        self.repo.delete_user_document.assert_called_once_with(
            "doc-a", "user-a"
        )

    def test_vector_failure(self):

        self.vector.delete_owned_chunks.return_value = False

        self.assertEqual(
            self.delete().status_code, 500
        )

        self.storage.delete_file.assert_not_called()
        self.repo.delete_user_document.assert_not_called()

    def test_storage_failure(self):

        self.storage.delete_file.side_effect = (
            RuntimeError("Storage failure")
        )

        self.assertEqual(
            self.delete().status_code, 500
        )

        self.repo.delete_user_document.assert_not_called()

    def test_database_failure(self):

        self.repo.delete_user_document.return_value = False

        self.assertEqual(
            self.delete().status_code, 500
        )

    def test_unsupported_storage(self):

        self.storage.get_storage_provider.return_value = (
            "supabase"
        )

        self.assertEqual(
            self.delete().status_code, 503
        )

        self.vector.delete_owned_chunks.assert_not_called()

    def test_unavailable_vector_backend(self):

        self.vector.collection = None

        self.assertEqual(
            self.delete().status_code, 503
        )

        self.storage.delete_file.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)