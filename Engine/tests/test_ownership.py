from app.infrastructure.database.repository import SQLiteRepository

repo = SQLiteRepository(db_path=":memory:")

user_a = "test-user-a"
user_b = "test-user-b"

workspace = repo.create_user_workspace(
    user_id=user_a,
    name="TCS Financial Analysis",
    description="Authentication testing"
)

workspace_id = workspace["workspace_id"]

assert repo.get_user_workspace(workspace_id, user_a) is not None
print("Test 1: Owner access - PASSED")

assert repo.get_user_workspace(workspace_id, user_b) is None
print("Test 2: Unauthorized access blocked - PASSED")

assert len(repo.list_user_workspaces(user_a)) == 1
print("Test 3: User A workspace listing - PASSED")

assert len(repo.list_user_workspaces(user_b)) == 0
print("Test 4: User B workspace isolation - PASSED")

print("\nAll ownership tests passed!")