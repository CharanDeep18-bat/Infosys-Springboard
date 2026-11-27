def get_owned_document_chunks(
    repository,
    vector_store,
    document_id,
    user_id
):
    if not user_id:
        raise ValueError("Authentication is required.")

    document = repository.get_user_document(
        document_id, user_id
    )

    if not document:
        raise ValueError("Document not found.")

    workspace_id = document["workspace_id"]

    chunks = vector_store.get_chunks_by_document(
        document_id,
        user_id=user_id,
        workspace_id=workspace_id
    )

    verified = []

    for chunk in chunks:
        metadata = chunk.get("metadata") or {}

        if (
            metadata.get("document_id") == document_id
            and metadata.get("user_id") == user_id
            and metadata.get("workspace_id") == workspace_id
        ):
            verified.append(chunk)

    return verified