from app.infrastructure.vector_store import get_vector_store
from app.infrastructure.database import get_database_repository

store = get_vector_store()
repo = get_database_repository()

if store.backend != "ChromaDB":
    raise SystemExit("Native ChromaDB is required for this audit.")

result = store.collection.get(
    include=["metadatas"]
)

verified = 0
unverified = 0

for chunk_id, metadata in zip(
    result["ids"],
    result["metadatas"]
):
    metadata = metadata or {}

    user_id = metadata.get("user_id")
    workspace_id = metadata.get("workspace_id")
    document_id = metadata.get("document_id")

    document = None

    if user_id and workspace_id and document_id:
        document = repo.get_user_document(
            document_id=document_id,
            user_id=user_id
        )

    if (
        document
        and document["workspace_id"] == workspace_id
        and chunk_id.startswith(document_id + "-")
    ):
        verified += 1
    else:
        unverified += 1

print("Total chunks:", len(result["ids"]))
print("Ownership metadata matches:", verified)
print("Unverified ownership metadata:", unverified)