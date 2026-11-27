"""Abstract Vector Store Interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
def validate_search_filters(filters):
    if not isinstance(filters, dict):
        raise ValueError("Ownership filters are required.")

    for field in ("user_id", "workspace_id", "document_id"):
        value = filters.get(field)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Valid {field} is required.")

    allowed = {
        "user_id",
        "workspace_id",
        "document_id",
        "is_table"
    }

    if set(filters) - allowed:
        raise ValueError("Unsupported vector search filter.")

    if (
        filters.get("is_table") is not None
        and not isinstance(filters["is_table"], bool)
    ):
        raise ValueError("is_table must be a boolean.")

    return dict(filters)
def validate_chunk_ownership(chunks: List[Dict[str, Any]]) -> None:
    required_fields = (
        "chunk_id",
        "document_id",
        "user_id",
        "workspace_id"
    )

    for chunk in chunks:
        for field in required_fields:
            value = chunk.get(field)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Chunk ownership validation failed: "
                    f"Missing or invalid {field}"
                )

        if not chunk["chunk_id"].startswith(
            chunk["document_id"] + "-"
        ):
            raise ValueError(
                "Chunk ID does not match document ID"
            )
class VectorStoreInterface(ABC):
    """Abstract interface for vector database operations."""

    @abstractmethod
    def upsert_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ) -> int:
        """Store chunk vectors and retrievable metadata payloads. Return count of upserted items."""
        pass

    @abstractmethod
    def search_chunks(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform semantic similarity search with optional metadata filtering."""
        pass

    @abstractmethod
    def count_chunks(self) -> int:
        """Return total count of indexed chunks in the primary collection."""
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """Verify vector database connectivity and collection health."""
        pass

    def get_chunks_by_document(
        self,
        document_id: str,
        *,
        user_id: str,
        workspace_id: str
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError

