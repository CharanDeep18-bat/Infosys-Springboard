import unittest
from unittest.mock import Mock, patch

from app.agents.document_agent.service import (
    DocumentAgentService
)


class TestSearchSecurity(unittest.TestCase):

    def setUp(self):

        self.service = object.__new__(
            DocumentAgentService
        )

        self.service.repo = Mock()
        self.service.vector_store = Mock()

        self.documents = {
            "doc-a": {
                "document_id": "doc-a",
                "user_id": "user-a",
                "workspace_id": "workspace-a",
                "indexed": True
            },
            "doc-b": {
                "document_id": "doc-b",
                "user_id": "user-b",
                "workspace_id": "workspace-b",
                "indexed": True
            },
            "doc-c": {
                "document_id": "doc-c",
                "user_id": "user-a",
                "workspace_id": "workspace-a",
                "indexed": True
            }
        }

        self.sessions = {
            "session-a": {
                "session_id": "session-a",
                "user_id": "user-a",
                "workspace_id": "workspace-a",
                "document_ids": ["doc-a"]
            },
            "session-b": {
                "session_id": "session-b",
                "user_id": "user-b",
                "workspace_id": "workspace-b",
                "document_ids": ["doc-b"]
            },
            "empty-session": {
                "session_id": "empty-session",
                "user_id": "user-a",
                "workspace_id": "workspace-a",
                "document_ids": []
            }
        }

        def owned_document(doc_id, user_id):
            doc = self.documents.get(doc_id)

            if doc and doc["user_id"] == user_id:
                return doc

            return None

        def owned_session(session_id, user_id):
            session = self.sessions.get(session_id)

            if session and session["user_id"] == user_id:
                return session

            return None

        self.service.repo.get_user_document.side_effect = (
            owned_document
        )

        self.service.repo.get_user_session.side_effect = (
            owned_session
        )

        self.service.repo.list_user_documents.side_effect = (
            lambda user_id: [
                d for d in self.documents.values()
                if d["user_id"] == user_id
            ]
        )

        self.service.vector_store.search_chunks.return_value = [
            self.chunk("doc-a", "user-a", "workspace-a"),
            self.chunk("doc-b", "user-b", "workspace-b"),
            self.chunk("doc-c", "user-a", "workspace-a"),
            {
                "chunk_id": "legacy-1",
                "text": "Unverified legacy data",
                "metadata": {"document_id": "doc-a"},
                "distance": 0.01
            }
        ]

        self.embedding_patch = patch(
            "app.agents.document_agent.service.generate_embeddings",
            return_value=[[1.0, 0.0, 0.0]]
        )

        self.embedding_patch.start()
        self.addCleanup(self.embedding_patch.stop)

    def chunk(self, doc_id, user_id, workspace_id):
        return {
            "chunk_id": doc_id + "-1",
            "text": "Financial evidence",
            "metadata": {
                "document_id": doc_id,
                "user_id": user_id,
                "workspace_id": workspace_id,
                "is_table": False
            },
            "distance": 0.1,
            "score": 0.9
        }

    def search(self, **kwargs):
        params = {
            "query": "Revenue",
            "user_id": "user-a"
        }

        params.update(kwargs)

        return self.service.search(**params)

    def result_ids(self, response):
        return [
            r.chunk_id for r in response.results
        ]

    def test_owned_document(self):
        result = self.search(document_id="doc-a")

        self.assertEqual(
            self.result_ids(result), ["doc-a-1"]
        )

    def test_cross_user_document(self):
        with self.assertRaises(ValueError):
            self.search(document_id="doc-b")

        self.service.vector_store.search_chunks.assert_not_called()

    def test_global_search(self):
        result = self.search()

        self.assertEqual(
            set(self.result_ids(result)),
            {"doc-a-1", "doc-c-1"}
        )

    def test_owned_session(self):
        result = self.search(session_id="session-a")

        self.assertEqual(
            self.result_ids(result), ["doc-a-1"]
        )

    def test_cross_user_session(self):
        with self.assertRaises(ValueError):
            self.search(session_id="session-b")

    def test_unattached_document(self):
        with self.assertRaises(ValueError):
            self.search(
                document_id="doc-c",
                session_id="session-a"
            )

    def test_empty_session(self):
        result = self.search(
            session_id="empty-session"
        )

        self.assertEqual(result.result_count, 0)

        self.service.vector_store.search_chunks.assert_not_called()

    def test_missing_user(self):
        with self.assertRaises(ValueError):
            self.search(user_id="")

    def test_empty_query(self):
        with self.assertRaises(ValueError):
            self.search(query="   ")

    def test_reverse_isolation(self):
        result = self.search(user_id="user-b")

        self.assertEqual(
            self.result_ids(result), ["doc-b-1"]
        )

    def test_legacy_exclusion(self):
        result = self.search(document_id="doc-a")

        self.assertNotIn(
            "legacy-1", self.result_ids(result)
        )

    def test_required_filters(self):
        self.search(document_id="doc-a")

        filters = (
            self.service.vector_store
            .search_chunks.call_args.kwargs["filters"]
        )

        self.assertEqual(filters, {
            "document_id": "doc-a",
            "user_id": "user-a",
            "workspace_id": "workspace-a"
        })

    def test_table_filter(self):
        result = self.search(
            document_id="doc-a",
            filter_tables_only=True
        )

        self.assertEqual(result.result_count, 0)

    def test_top_k_limit(self):
        result = self.search(top_k=1)

        self.assertEqual(result.result_count, 1)

    def test_no_global_database_lookup(self):
        self.search()

        self.service.repo.list_documents.assert_not_called()
        self.service.repo.get_document_by_id.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)