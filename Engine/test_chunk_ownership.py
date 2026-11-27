from app.infrastructure.vector_store.base import (
    validate_chunk_ownership
)

chunk = {
    "chunk_id": "doc-a-1",
    "document_id": "doc-a",
    "user_id": "user-a",
    "workspace_id": "workspace-a",
    "text": "Sample financial data"
}

validate_chunk_ownership([chunk])
print("Valid chunk: PASSED")

for field in [
    "user_id",
    "workspace_id",
    "document_id",
    "chunk_id"
]:
    invalid = chunk.copy()
    invalid.pop(field)

    try:
        validate_chunk_ownership([invalid])
    except ValueError:
        print(f"Missing {field} rejected: PASSED")
    else:
        raise AssertionError(f"Missing {field} accepted")

invalid = chunk.copy()
invalid["chunk_id"] = "another-document-1"

try:
    validate_chunk_ownership([invalid])
except ValueError:
    print("Mismatched chunk ID rejected: PASSED")
else:
    raise AssertionError("Mismatched chunk ID accepted")

print("\nAll chunk ownership tests passed!")