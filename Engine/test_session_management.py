import unittest

from unittest.mock import patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.infrastructure.database.repository import (
    SQLiteRepository
)

from app.api.routes import workspaces
from app.api.dependencies.auth import get_current_user


class TestSessionManagement(unittest.TestCase):

    def setUp(self):

        self.repo = SQLiteRepository(":memory:")

        self.wa = self.repo.create_user_workspace(
            user_id="user-a",
            name="Workspace A",
            description=""
        )

        self.wb = self.repo.create_user_workspace(
            user_id="user-b",
            name="Workspace B",
            description=""
        )

        self.sa = self.repo.create_user_session(
            workspace_id=self.wa["workspace_id"],
            user_id="user-a",
            title="Session A",
            description="Original A"
        )

        self.sb = self.repo.create_user_session(
            workspace_id=self.wb["workspace_id"],
            user_id="user-b",
            title="Session B",
            description="Original B"
        )

        self.a = self.sa["session_id"]
        self.b = self.sb["session_id"]

        self.app = FastAPI()
        self.app.include_router(workspaces.router)

        self.app.dependency_overrides[get_current_user] = (
            lambda: {"id": "user-a"}
        )

        p = patch.object(
            workspaces,
            "get_database_repository",
            return_value=self.repo
        )

        p.start()
        self.addCleanup(p.stop)

        self.client = TestClient(self.app)

    def update(self, session_id, title="Updated Session"):

        return self.client.patch(
            f"/sessions/{session_id}",
            json={
                "title": title,
                "description": "Updated description"
            }
        )

    def delete(self, session_id):

        return self.client.delete(
            f"/sessions/{session_id}"
        )

    def test_owned_update(self):

        response = self.update(self.a)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["title"],
            "Updated Session"
        )

    def test_update_persisted(self):

        self.update(self.a)

        session = self.repo.get_user_session(
            self.a, "user-a"
        )

        self.assertEqual(
            session["title"],
            "Updated Session"
        )

        self.assertEqual(
            session["description"],
            "Updated description"
        )

    def test_cross_user_update(self):

        self.assertEqual(
            self.update(self.b).status_code, 404
        )

        session = self.repo.get_user_session(
            self.b, "user-b"
        )

        self.assertEqual(session["title"], "Session B")

    def test_owned_delete(self):

        self.assertEqual(
            self.delete(self.a).status_code, 200
        )

        self.assertIsNone(
            self.repo.get_user_session(
                self.a, "user-a"
            )
        )

    def test_cross_user_delete(self):

        self.assertEqual(
            self.delete(self.b).status_code, 404
        )

        self.assertIsNotNone(
            self.repo.get_user_session(
                self.b, "user-b"
            )
        )

    def test_other_session_preserved(self):

        self.delete(self.a)

        self.assertIsNotNone(
            self.repo.get_user_session(
                self.b, "user-b"
            )
        )

    def test_workspace_preserved(self):

        self.delete(self.a)

        self.assertIsNotNone(
            self.repo.get_user_workspace(
                self.wa["workspace_id"],
                "user-a"
            )
        )

    def test_deleted_session_not_listed(self):

        self.delete(self.a)

        sessions = self.repo.list_user_sessions(
            self.wa["workspace_id"],
            "user-a"
        )

        self.assertNotIn(
            self.a,
            [s["session_id"] for s in sessions]
        )

    def test_repeated_delete(self):

        self.delete(self.a)

        self.assertEqual(
            self.delete(self.a).status_code, 404
        )

    def test_empty_title(self):

        self.assertEqual(
            self.update(self.a, "").status_code,
            422
        )

    def test_whitespace_title(self):

        self.assertEqual(
            self.update(self.a, "   ").status_code,
            400
        )

    def test_unauthenticated(self):

        def unauthorized():
            raise HTTPException(status_code=401)

        self.app.dependency_overrides[get_current_user] = (
            unauthorized
        )

        self.assertEqual(
            self.update(self.a).status_code, 401
        )

        self.assertEqual(
            self.delete(self.a).status_code, 401
        )

    def test_reverse_account_isolation(self):

        self.app.dependency_overrides[get_current_user] = (
            lambda: {"id": "user-b"}
        )

        self.assertEqual(
            self.update(self.a).status_code, 404
        )

        self.assertEqual(
            self.update(self.b).status_code, 200
        )

    def test_database_integrity(self):

        self.delete(self.a)

        with self.repo._get_connection() as conn:

            errors = conn.execute(
                "PRAGMA foreign_key_check"
            ).fetchall()

        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)