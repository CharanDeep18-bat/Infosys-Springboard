from unittest.mock import patch

from app.infrastructure.database.repository import SQLiteRepository

from app.orchestration.workflow import MultiAgentWorkflowOrchestrator

repo = SQLiteRepository(db_path=":memory:")

user_a = "test-user-a"
user_b = "test-user-b"

ws_a = repo.create_user_workspace(user_a, "Workspace A")
ws_b = repo.create_user_workspace(user_b, "Workspace B")

repo.create_document({
    "document_id": "doc-a",
    "workspace_id": ws_a["workspace_id"],
    "user_id": user_a,
    "filename": "sample.pdf",
    "stored_filename": "sample.pdf",
    "storage_path": "sample.pdf",
    "sha256": "a" * 64,
    "total_pages": 10,
    "metadata": {}
})


def check(name, expected, error_type=ValueError, **kwargs):
    try:
        MultiAgentWorkflowOrchestrator.run_pipeline(
            document_id="doc-a",
            filename="sample.pdf",
            **kwargs
        )

    except error_type as exc:
        assert expected in str(exc), str(exc)
        print(name + ": PASSED")
        return

    raise AssertionError(name + ": FAILED")


with patch(
    "app.orchestration.workflow.get_database_repository",
    return_value=repo
):

    check(
        "Missing user",
        "Authenticated user ID is required"
    )

    check(
        "Cross-user document",
        "Document not found",
        user_id=user_b
    )

    check(
        "Workspace mismatch",
        "Document not found in workspace",
        user_id=user_a,
        workspace_id=ws_b["workspace_id"]
    )

    check(
        "Invalid session",
        "Research session not found",
        user_id=user_a,
        session_id="invalid-session"
    )

    check(
        "Invalid processing job",
        "Processing job not found",
        user_id=user_a,
        job_id="invalid-job"
    )

    check(
        "Direct file substitution",
        "Direct file bytes are not accepted",
        user_id=user_a,
        file_bytes=b"test"
    )

    check(
        "Authorized workflow safely restricted",
        "Secure workflow execution is temporarily disabled",
        error_type=RuntimeError,
        user_id=user_a
    )

print("\nAll workflow authorization tests passed!")