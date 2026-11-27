from tempfile import TemporaryDirectory

from app.infrastructure.vector_store.chroma import (
    ChromaVectorStore
)

from app.infrastructure.vector_store.fallback import (
    LocalJSONVectorStore
)

from app.infrastructure.vector_store.qdrant import (
    QdrantVectorStore
)

passed = 0
failed = 0


def check(name, condition):
    global passed, failed

    if condition:
        passed += 1
        print(f"[PASS] {name}")
    else:
        failed += 1
        print(f"[FAIL] {name}")


def rejected(function, error=ValueError):
    try:
        function()
    except error:
        return True

    return False


def run_tests(store):

    name = type(store).__name__

    print(f"\n--- {name} ---")

    chunks = [
        {
            "chunk_id": "doc-a-1",
            "document_id": "doc-a",
            "user_id": "user-a",
            "workspace_id": "workspace-a",
            "text": "Account A revenue",
            "is_table": False
        },
        {
            "chunk_id": "doc-b-1",
            "document_id": "doc-b",
            "user_id": "user-b",
            "workspace_id": "workspace-b",
            "text": "Account B revenue",
            "is_table": True
        }
    ]

    embeddings = [
        [1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0]
    ]

    store.upsert_chunks(chunks, embeddings)

    query = [1.0, 0.0, 0.0]

    scope_a = {
        "user_id": "user-a",
        "workspace_id": "workspace-a",
        "document_id": "doc-a"
    }

    scope_b = {
        "user_id": "user-b",
        "workspace_id": "workspace-b",
        "document_id": "doc-b"
    }

    results = store.search_chunks(
        query, filters=scope_a
    )

    check(
        "Account A retrieves only its chunk",
        [r["chunk_id"] for r in results] == ["doc-a-1"]
    )

    results = store.search_chunks(
        query, filters=scope_b
    )

    check(
        "Account B retrieves only its chunk",
        [r["chunk_id"] for r in results] == ["doc-b-1"]
    )

    check(
        "Cross-user search blocked",
        not store.search_chunks(
            query,
            filters={**scope_b, "user_id": "user-a"}
        )
    )

    check(
        "Wrong workspace blocked",
        not store.search_chunks(
            query,
            filters={**scope_a, "workspace_id": "workspace-b"}
        )
    )

    check(
        "Unscoped search rejected",
        rejected(lambda: store.search_chunks(query))
    )

    check(
        "Missing user ID rejected",
        rejected(lambda: store.search_chunks(
            query,
            filters={"document_id": "doc-a"}
        ))
    )

    check(
        "Empty user ID rejected",
        rejected(lambda: store.search_chunks(
            query,
            filters={**scope_a, "user_id": ""}
        ))
    )

    check(
        "Missing workspace rejected",
        rejected(lambda: store.search_chunks(
            query,
            filters={
                "user_id": "user-a",
                "document_id": "doc-a"
            }
        ))
    )

    check(
        "Missing document ID rejected",
        rejected(lambda: store.search_chunks(
            query,
            filters={
                "user_id": "user-a",
                "workspace_id": "workspace-a"
            }
        ))
    )

    results = store.get_chunks_by_document(
        "doc-a",
        user_id="user-a",
        workspace_id="workspace-a"
    )

    check(
        "Owned direct retrieval works",
        [r["chunk_id"] for r in results] == ["doc-a-1"]
    )

    check(
        "Cross-user direct retrieval blocked",
        not store.get_chunks_by_document(
            "doc-b",
            user_id="user-a",
            workspace_id="workspace-b"
        )
    )

    check(
        "Direct retrieval requires ownership",
        rejected(
            lambda: store.get_chunks_by_document("doc-a"),
            TypeError
        )
    )

    check(
        "Table filtering works",
        not store.search_chunks(
            query,
            filters={**scope_a, "is_table": True}
        )
    )

    invalid = chunks[0].copy()
    invalid.pop("user_id")

    check(
        "Indexing without owner rejected",
        rejected(lambda: store.upsert_chunks(
            [invalid], [query]
        ))
    )

    legacy_metadata = {
        "document_id": "doc-a",
        "workspace_id": "workspace-a"
    }

    if isinstance(store, ChromaVectorStore):
        store.collection.upsert(
            ids=["doc-a-legacy"],
            documents=["Legacy financial data"],
            embeddings=[query],
            metadatas=[legacy_metadata]
        )
    else:
        store._records["doc-a-legacy"] = {
            "text": "Legacy financial data",
            "embedding": query,
            "metadata": legacy_metadata
        }

    results = store.search_chunks(
        query, filters=scope_a
    )

    check(
        "Legacy chunks excluded from search",
        [r["chunk_id"] for r in results] == ["doc-a-1"]
    )

    results = store.get_chunks_by_document(
        "doc-a",
        user_id="user-a",
        workspace_id="workspace-a"
    )

    check(
        "Legacy chunks excluded from direct retrieval",
        [r["chunk_id"] for r in results] == ["doc-a-1"]
    )


with TemporaryDirectory(ignore_cleanup_errors=True) as directory:
    chroma = ChromaVectorStore(
        persist_dir=directory,
        collection_name="security_test"
    )

    if chroma.backend != "ChromaDB":
        raise RuntimeError("Native ChromaDB is not active.")

    run_tests(chroma)


with TemporaryDirectory(ignore_cleanup_errors=True) as directory:
    fallback = LocalJSONVectorStore(
        persist_dir=directory,
        collection_name="security_test"
    )

    run_tests(fallback)


print("\n--- Qdrant restrictions ---")

qdrant = object.__new__(QdrantVectorStore)

check(
    "Qdrant semantic search disabled",
    rejected(
        lambda: qdrant.search_chunks([1.0, 0.0, 0.0]),
        RuntimeError
    )
)

check(
    "Qdrant direct retrieval disabled",
    rejected(
        lambda: qdrant.get_chunks_by_document(
            "doc-a",
            user_id="user-a",
            workspace_id="workspace-a"
        ),
        RuntimeError
    )
)

print("\n==============================")
print(f"Total tests : {passed + failed}")
print(f"Passed      : {passed}")
print(f"Failed      : {failed}")
print("==============================")

if failed:
    raise SystemExit(1)

print("ALL VECTOR ISOLATION TESTS PASSED!")