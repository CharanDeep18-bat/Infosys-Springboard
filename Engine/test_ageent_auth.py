from unittest.mock import patch

from fastapi import HTTPException

from app.infrastructure.database.repository import SQLiteRepository

from app.api.dependencies.ownership import (
    require_owned_workspace,
    require_owned_session,
    require_owned_document,
    require_owned_documents,
    require_session_documents
)

repo = SQLiteRepository(db_path=":memory:")

user_a = "test-user-a"
user_b = "test-user-b"

ws_a = repo.create_user_workspace(user_a, "Workspace A")
ws_b = repo.create_user_workspace(user_b, "Workspace B")

session_a = repo.create_user_session(
    workspace_id=ws_a["workspace_id"],
    user_id=user_a,
    title="Research A"
)

session_b = repo.create_user_session(
    workspace_id=ws_b["workspace_id"],
    user_id=user_b,
    title="Research B"
)


def create_doc(doc_id, user_id, workspace_id, file_hash):
    return repo.create_document({
        "document_id": doc_id,
        "workspace_id": workspace_id,
        "user_id": user_id,
        "filename": doc_id + ".pdf",
        "stored_filename": doc_id + ".pdf",
        "storage_path": doc_id + ".pdf",
        "sha256": file_hash,
        "total_pages": 10,
        "metadata": {}
    })


create_doc("doc-a", user_a, ws_a["workspace_id"], "a" * 64)
create_doc("doc-b", user_b, ws_b["workspace_id"], "b" * 64)


def expect_error(function, status_code, *args):
    try:
        function(*args)

    except HTTPException as exc:
        assert exc.status_code == status_code
        return

    raise AssertionError("Unauthorized operation was accepted")


with patch(
    "app.api.dependencies.ownership.get_database_repository",
    return_value=repo
):

    assert require_owned_workspace(
        ws_a["workspace_id"], user_a
    )

    print("Test 1: Owned workspace - PASSED")

    expect_error(
        require_owned_workspace,
        404,
        ws_a["workspace_id"],
        user_b
    )

    print("Test 2: Cross-user workspace blocked - PASSED")

    assert require_owned_session(
        session_a["session_id"], user_a
    )

    print("Test 3: Owned session - PASSED")

    expect_error(
        require_owned_session,
        404,
        session_a["session_id"],
        user_b
    )

    print("Test 4: Cross-user session blocked - PASSED")

    assert require_owned_document("doc-a", user_a)

    print("Test 5: Owned document - PASSED")

    expect_error(
        require_owned_document,
        404,
        "doc-a",
        user_b
    )

    print("Test 6: Cross-user document blocked - PASSED")

    assert len(
        require_owned_documents(["doc-a"], user_a)
    ) == 1

    print("Test 7: Multiple document validation - PASSED")

    expect_error(
        require_owned_documents,
        404,
        ["doc-a", "doc-b"],
        user_a
    )

    print("Test 8: Mixed-owner documents blocked - PASSED")

    expect_error(
        require_owned_documents,
        400,
        [],
        user_a
    )

    print("Test 9: Empty document list blocked - PASSED")

    expect_error(
        require_owned_documents,
        404,
        ["doc-a"],
        user_a,
        ws_b["workspace_id"]
    )

    print("Test 10: Workspace mismatch blocked - PASSED")

    expect_error(
        require_session_documents,
        404,
        session_a["session_id"],
        ["doc-a"],
        user_a
    )

    print("Test 11: Unattached session document blocked - PASSED")

    expect_error(
        require_session_documents,
        404,
        session_b["session_id"],
        ["doc-a"],
        user_a
    )

    print("Test 12: Unauthorized session context blocked - PASSED")

print("\nAll agent authorization tests passed!")