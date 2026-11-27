import unittest

from app.infrastructure.database.repository import (
    SQLiteRepository
)


class TestSessionFeatures(unittest.TestCase):

    def setUp(self):

        self.repo = SQLiteRepository(":memory:")

        self.workspace = self.repo.create_user_workspace(
            user_id="user-a",
            name="Workspace A",
            description=""
        )

        self.session = self.repo.create_user_session(
            workspace_id=self.workspace["workspace_id"],
            user_id="user-a",
            title="Research",
            description="Financial analysis"
        )

        self.sid = self.session["session_id"]

        self.metadata = {
            "company": "Infosys",
            "researchType": "Financial Analysis",
            "objective": "Analyze revenue"
        }

    def save_metadata(self):

        return self.repo.update_user_session_metadata(
            self.sid,
            "user-a",
            self.metadata
        )

    def test_metadata_saved(self):

        self.assertTrue(self.save_metadata())

        result = self.repo.get_user_session(
            self.sid, "user-a"
        )

        self.assertEqual(
            result["metadata"], self.metadata
        )

    def test_metadata_in_session_list(self):

        self.save_metadata()

        result = self.repo.list_user_sessions(
            self.workspace["workspace_id"],
            "user-a"
        )

        self.assertEqual(
            result[0]["metadata"], self.metadata
        )

    def test_cross_user_metadata_update(self):

        result = self.repo.update_user_session_metadata(
            self.sid,
            "user-b",
            self.metadata
        )

        self.assertFalse(result)

    def test_untrusted_metadata_removed(self):

        self.metadata["user_id"] = "user-b"
        self.metadata["workspace_id"] = "fake"

        self.save_metadata()

        result = self.repo.get_user_session(
            self.sid, "user-a"
        )

        self.assertNotIn(
            "user_id", result["metadata"]
        )

        self.assertNotIn(
            "workspace_id", result["metadata"]
        )

    def test_duplicate_session(self):

        result = self.repo.duplicate_user_session(
            self.sid, "user-a"
        )

        self.assertIsNotNone(result)

        self.assertNotEqual(
            result["session_id"], self.sid
        )

        self.assertEqual(
            result["title"], "Research (Copy)"
        )

    def test_duplicate_metadata(self):

        self.save_metadata()

        result = self.repo.duplicate_user_session(
            self.sid, "user-a"
        )

        self.assertEqual(
            result["metadata"], self.metadata
        )

    def test_duplicate_workspace(self):

        result = self.repo.duplicate_user_session(
            self.sid, "user-a"
        )

        self.assertEqual(
            result["workspace_id"],
            self.workspace["workspace_id"]
        )

    def test_cross_user_duplication(self):

        self.assertIsNone(
            self.repo.duplicate_user_session(
                self.sid, "user-b"
            )
        )

    def test_original_session_preserved(self):

        self.repo.duplicate_user_session(
            self.sid, "user-a"
        )

        result = self.repo.get_user_session(
            self.sid, "user-a"
        )

        self.assertEqual(result["title"], "Research")

    def test_database_integrity(self):

        self.repo.duplicate_user_session(
            self.sid, "user-a"
        )

        with self.repo._get_connection() as conn:

            errors = conn.execute(
                "PRAGMA foreign_key_check"
            ).fetchall()

        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)