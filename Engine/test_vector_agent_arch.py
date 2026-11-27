import unittest
from unittest.mock import Mock

from app.infrastructure.vector_store.ownership import (
    get_owned_document_chunks
)


class TestAgentVectorSecurity(unittest.TestCase):

    def setUp(self):
        self.repo = Mock()
        self.vector = Mock()

        self.repo.get_user_document.side_effect = (
            lambda doc, user: {
                "document_id": "doc-a",
                "user_id": "user-a",
                "workspace_id": "workspace-a"
            } if doc == "doc-a" and user == "user-a"
            else None
        )

        self.vector.get_chunks_by_document.return_value = [
            self.chunk("doc-a", "user-a", "workspace-a"),
            self.chunk("doc-b", "user-b", "workspace-b"),
            self.chunk("doc-a", "user-b", "workspace-a"),
            self.chunk("doc-a", "user-a", "workspace-b"),
            {
                "chunk_id": "legacy",
                "text": "Legacy data",
                "metadata": {"document_id": "doc-a"}
            }
        ]

    def chunk(self, doc, user, workspace):
        return {
            "chunk_id": doc + "-1",
            "text": "Financial evidence",
            "metadata": {
                "document_id": doc,
                "user_id": user,
                "workspace_id": workspace
            }
        }

    def retrieve(self, doc="doc-a", user="user-a"):
        return get_owned_document_chunks(
            self.repo,
            self.vector,
            doc,
            user
        )

    def test_owned_document(self):
        results = self.retrieve()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["chunk_id"], "doc-a-1")

    def test_cross_user_document(self):
        with self.assertRaises(ValueError):
            self.retrieve("doc-b")

        self.vector.get_chunks_by_document.assert_not_called()

    def test_reverse_isolation(self):
        with self.assertRaises(ValueError):
            self.retrieve(user="user-b")

    def test_missing_user(self):
        with self.assertRaises(ValueError):
            self.retrieve(user="")

    def test_required_filters(self):
        self.retrieve()

        self.vector.get_chunks_by_document.assert_called_once_with(
            "doc-a",
            user_id="user-a",
            workspace_id="workspace-a"
        )

    def test_wrong_owner_metadata(self):
        results = self.retrieve()

        self.assertTrue(all(
            r["metadata"]["user_id"] == "user-a"
            for r in results
        ))

    def test_wrong_workspace_metadata(self):
        results = self.retrieve()

        self.assertTrue(all(
            r["metadata"]["workspace_id"] == "workspace-a"
            for r in results
        ))

    def test_wrong_document_metadata(self):
        results = self.retrieve()

        self.assertTrue(all(
            r["metadata"]["document_id"] == "doc-a"
            for r in results
        ))

    def test_legacy_exclusion(self):
        results = self.retrieve()

        self.assertNotIn(
            "legacy",
            [r["chunk_id"] for r in results]
        )

    def test_empty_vector_results(self):
        self.vector.get_chunks_by_document.return_value = []

        self.assertEqual(self.retrieve(), [])

    def test_vector_failure(self):
        self.vector.get_chunks_by_document.side_effect = (
            RuntimeError("Vector store unavailable")
        )

        with self.assertRaises(RuntimeError):
            self.retrieve()


if __name__ == "__main__":
    unittest.main(verbosity=2)