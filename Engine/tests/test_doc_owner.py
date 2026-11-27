from app.infrastructure.database.repository import SQLiteRepository

repo = SQLiteRepository(db_path=":memory:")

user_a = "test-user-a"
user_b = "test-user-b"

workspace = repo.create_user_workspace(
    user_id=user_a,
    name="Document Test Workspace"
)

workspace_id = workspace["workspace_id"]

doc = repo.create_document({
    "document_id": "test-doc-001",
    "workspace_id": workspace_id,
    "user_id": user_a,
    "filename": "annual_report.pdf",
    "stored_filename": "test-doc-001.pdf",
    "sha256": "a" * 64,
    "storage_path": "test-path",
    "total_pages": 10,
    "metadata": {}
})

document_id = doc["document_id"]

assert repo.get_user_document(document_id, user_a) is not None
print("Test 1: Owner document access - PASSED")

assert repo.get_user_document(document_id, user_b) is None
print("Test 2: Unauthorized document access blocked - PASSED")

assert len(repo.list_user_documents(user_a)) == 1
print("Test 3: Owner document listing - PASSED")

assert len(repo.list_user_documents(user_b)) == 0
print("Test 4: Document listing isolation - PASSED")

assert repo.get_user_document_by_sha256("a" * 64, user_a) is not None
print("Test 5: Owner hash lookup - PASSED")

assert repo.get_user_document_by_sha256("a" * 64, user_b) is None
print("Test 6: Cross-user hash lookup blocked - PASSED")

print("\nAll document ownership tests passed!")