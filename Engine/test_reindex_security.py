import hashlib
import unittest

from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.agents.document_agent.service import (
    DocumentAgentService
)


class TestReindexSecurity(unittest.TestCase):

    def setUp(self):

        self.service = object.__new__(
            DocumentAgentService
        )

        self.service.repo = Mock()
        self.service.storage = Mock()
        self.service.parser = Mock()
        self.service.chunker = Mock()
        self.service.vector_store = Mock()

        self.service.settings = SimpleNamespace(
            max_file_size=1000000
        )

        self.pdf = b"Sample PDF bytes"

        self.document = {
            "document_id": "doc-a",
            "user_id": "user-a",
            "workspace_id": "workspace-a",
            "filename": "report.pdf",
            "sha256": hashlib.sha256(
                self.pdf
            ).hexdigest(),
            "metadata": {
                "object_key": "doc-a.pdf"
            }
        }

        self.service.repo.get_user_document.side_effect = (
            lambda doc, user: self.document
            if doc == "doc-a" and user == "user-a"
            else None
        )

        self.service.storage.get_file_bytes.return_value = (
            self.pdf
        )

        self.service.parser.parse_pdf.return_value = [
            SimpleNamespace(
                text="Revenue is 100",
                tables=[]
            )
        ]

        self.service.chunker.chunk_pages.return_value = [
            {
                "chunk_id": "doc-a-1",
                "document_id": "doc-a",
                "text": "Revenue is 100"
            }
        ]

        self.service.vector_store.get_chunks_by_document.return_value = [
            {
                "chunk_id": "doc-a-1",
                "metadata": {
                    "document_id": "doc-a",
                    "user_id": "user-a",
                    "workspace_id": "workspace-a"
                }
            }
        ]

        embedding_patch = patch(
            "app.agents.document_agent.service.generate_embeddings",
            return_value=[[1.0, 0.0, 0.0]]
        )

        dimension_patch = patch(
            "app.agents.document_agent.service.get_embedding_dimension",
            return_value=3
        )

        embedding_patch.start()
        dimension_patch.start()

        self.addCleanup(embedding_patch.stop)
        self.addCleanup(dimension_patch.stop)

    def reindex(self, doc="doc-a", user="user-a"):

        return self.service.reindex_owned_document(
            doc,
            user_id=user
        )

    def test_owned_reindex(self):

        result = self.reindex()

        self.assertTrue(result["indexed"])
        self.assertEqual(result["chunk_count"], 1)

    def test_document_id_preserved(self):

        self.assertEqual(
            self.reindex()["document_id"],
            "doc-a"
        )

    def test_cross_user_rejected(self):

        with self.assertRaises(ValueError):
            self.reindex(user="user-b")

        self.service.storage.get_file_bytes.assert_not_called()

    def test_missing_user_rejected(self):

        with self.assertRaises(ValueError):
            self.reindex(user="")

    def test_unknown_document_rejected(self):

        with self.assertRaises(ValueError):
            self.reindex(doc="unknown")

    def test_missing_pdf_rejected(self):

        self.service.storage.get_file_bytes.return_value = None

        with self.assertRaises(ValueError):
            self.reindex()

    def test_modified_pdf_rejected(self):

        self.service.storage.get_file_bytes.return_value = (
            b"Modified PDF"
        )

        with self.assertRaises(ValueError):
            self.reindex()

        self.service.vector_store.upsert_chunks.assert_not_called()

    def test_ownership_metadata(self):

        self.reindex()

        chunks = (
            self.service.vector_store
            .upsert_chunks.call_args.args[0]
        )

        self.assertEqual(
            chunks[0]["user_id"], "user-a"
        )

        self.assertEqual(
            chunks[0]["workspace_id"], "workspace-a"
        )

    def test_empty_chunks_rejected(self):

        self.service.chunker.chunk_pages.return_value = []

        with self.assertRaises(ValueError):
            self.reindex()

    def test_index_verification_failure(self):

        self.service.vector_store.get_chunks_by_document.return_value = []

        with self.assertRaises(RuntimeError):
            self.reindex()

        self.service.repo.update_document_indexed.assert_not_called()

    def test_no_new_document_created(self):

        self.reindex()

        self.service.repo.create_document.assert_not_called()
        self.service.storage.save_file.assert_not_called()

    def test_database_updated(self):

        self.reindex()

        args = (
            self.service.repo
            .update_document_indexed.call_args.kwargs
        )

        self.assertEqual(args["document_id"], "doc-a")
        self.assertEqual(args["indexed"], 1)
        self.assertEqual(args["chunk_count"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)