from app.infrastructure.database.repository import SQLiteRepository

repo = SQLiteRepository(db_path=":memory:")

user_a = "test-user-a"
user_b = "test-user-b"

ws_a = repo.create_user_workspace(user_a, "Workspace A")
ws_b = repo.create_user_workspace(user_b, "Workspace B")

same_hash = "a" * 64

def create_doc(doc_id, user_id, workspace_id):
    return repo.create_document({
        "document_id": doc_id,
        "workspace_id": workspace_id,
        "user_id": user_id,
        "filename": "annual_report.pdf",
        "stored_filename": doc_id + ".pdf",
        "sha256": same_hash,
        "storage_path": doc_id + ".pdf",
        "total_pages": 10,
        "metadata": {}
    })

doc_a = create_doc(
    "doc-a", user_a, ws_a["workspace_id"]
)

print("Test 1: User A document created - PASSED")

doc_b = create_doc(
    "doc-b", user_b, ws_b["workspace_id"]
)

print("Test 2: User B same PDF created - PASSED")

assert repo.get_user_document("doc-a", user_a)
assert repo.get_user_document("doc-b", user_b)

print("Test 3: Both documents preserved - PASSED")

try:
    create_doc("doc-a2", user_a, ws_a["workspace_id"])
except ValueError as e:
    assert str(e) == "Document already exists for this user"
    print("Test 4: Same-user duplicate blocked - PASSED")
else:
    raise AssertionError("Duplicate was not blocked")

assert repo.get_user_document("doc-a", user_b) is None
assert repo.get_user_document("doc-b", user_a) is None

print("Test 5: Cross-user access blocked - PASSED")

try:
    create_doc("doc-c", user_b, ws_a["workspace_id"])
except ValueError as e:
    assert str(e) == "Workspace not found"
    print("Test 6: Unauthorized workspace blocked - PASSED")
else:
    raise AssertionError("Unauthorized workspace accepted")

try:
    create_doc("doc-a", user_b, ws_b["workspace_id"])
except ValueError as e:
    assert str(e) == "Document ownership conflict"
    print("Test 7: Cross-user overwrite blocked - PASSED")
else:
    raise AssertionError("Unauthorized overwrite accepted")

print("\nAll deduplication tests passed!")