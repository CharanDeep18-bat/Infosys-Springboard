from unittest.mock import Mock, patch

from app.agents.research_agent.service import (
    ResearchAgentService
)

repo = Mock()
vector = Mock()

documents = {
    "doc-a": {
        "document_id": "doc-a",
        "user_id": "user-a",
        "workspace_id": "workspace-a",
        "indexed": True,
        "filename": "A.pdf"
    },
    "doc-b": {
        "document_id": "doc-b",
        "user_id": "user-b",
        "workspace_id": "workspace-b",
        "indexed": True,
        "filename": "B.pdf"
    },
    "doc-c": {
        "document_id": "doc-c",
        "user_id": "user-a",
        "workspace_id": "workspace-a",
        "indexed": True,
        "filename": "C.pdf"
    }
}

sessions = {
    "session-a": {
        "session_id": "session-a",
        "user_id": "user-a",
        "workspace_id": "workspace-a",
        "document_ids": ["doc-a"]
    },
    "session-b": {
        "session_id": "session-b",
        "user_id": "user-b",
        "workspace_id": "workspace-b",
        "document_ids": ["doc-b"]
    },
    "empty-session": {
        "session_id": "empty-session",
        "user_id": "user-a",
        "workspace_id": "workspace-a",
        "document_ids": []
    }
}


def owned_document(doc_id, user_id):
    doc = documents.get(doc_id)

    if doc and doc["user_id"] == user_id:
        return doc

    return None


def owned_session(session_id, user_id):
    session = sessions.get(session_id)

    if session and session["user_id"] == user_id:
        return session

    return None


repo.get_user_document.side_effect = owned_document

repo.get_user_session.side_effect = owned_session

repo.list_user_documents.side_effect = (
    lambda user_id: [
        d for d in documents.values()
        if d["user_id"] == user_id
    ]
)

repo.get_financial_metrics.return_value = []
repo.get_red_flag_findings.return_value = []

service = ResearchAgentService(
    repository=repo,
    vector_store=vector
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


def rejected(function):
    try:
        function()
    except ValueError:
        return True

    return False


def resolve(ids=None, session=None, user="user-a"):
    return service._resolve_documents(
        document_ids=ids,
        session_id=session,
        user_id=user
    )


def ids(result):
    return [d["document_id"] for d in result]


check(
    "Owned document resolution",
    ids(resolve(["doc-a"])) == ["doc-a"]
)

check(
    "Cross-user document rejected",
    rejected(lambda: resolve(["doc-b"]))
)

check(
    "Mixed-owner documents rejected",
    rejected(lambda: resolve(["doc-a", "doc-b"]))
)

check(
    "Global research restricted to owner",
    ids(resolve()) == ["doc-a", "doc-c"]
)

check(
    "Owned session resolution",
    ids(resolve(session="session-a")) == ["doc-a"]
)

check(
    "Cross-user session rejected",
    rejected(lambda: resolve(session="session-b"))
)

check(
    "Unattached document rejected",
    rejected(
        lambda: resolve(["doc-c"], "session-a")
    )
)

check(
    "Empty session does not fall back",
    resolve(session="empty-session") == []
)

check(
    "Empty selection does not fall back",
    resolve([]) == []
)

check(
    "Duplicate documents removed",
    ids(resolve(["doc-a", "doc-a"])) == ["doc-a"]
)

check(
    "Missing user rejected",
    rejected(lambda: resolve(user=""))
)

check(
    "Reverse account isolation",
    ids(resolve(user="user-b")) == ["doc-b"]
)

vector.search_chunks.return_value = [
    {
        "chunk_id": "doc-a-1",
        "text": "Owned financial evidence",
        "metadata": {
            "document_id": "doc-a",
            "user_id": "user-a",
            "workspace_id": "workspace-a",
            "page_number": 1
        },
        "score": 0.9
    },
    {
        "chunk_id": "doc-b-1",
        "text": "Unauthorized financial evidence",
        "metadata": {
            "document_id": "doc-b",
            "user_id": "user-b",
            "workspace_id": "workspace-b",
            "page_number": 1
        },
        "score": 0.99
    },
    {
        "chunk_id": "doc-a-legacy",
        "text": "Unverified legacy evidence",
        "metadata": {
            "document_id": "doc-a"
        },
        "score": 0.95
    }
]

with patch(
    "app.agents.research_agent.service.generate_embeddings",
    return_value=[[1.0, 0.0, 0.0]]
):

    results = service._retrieve_chunks(
        ["Revenue"],
        "doc-a",
        5,
        user_id="user-a",
        workspace_id="workspace-a"
    )

    check(
        "Only authorized vector evidence returned",
        len(results) == 1
        and results[0]["chunk_id"] == "doc-a-1"
    )

    filters = vector.search_chunks.call_args.kwargs["filters"]

    check(
        "Mandatory ownership filters passed",
        filters == {
            "document_id": "doc-a",
            "user_id": "user-a",
            "workspace_id": "workspace-a"
        }
    )

    answer = service.answer_question(
        question="Summarize revenue",
        document_ids=["doc-a"],
        user_id="user-a"
    )

    check(
        "Research answer generated",
        bool(answer.answer)
    )

    check(
        "Only owned document used",
        answer.documents_used == ["A.pdf"]
    )

    check(
        "Unauthorized evidence excluded from answer",
        "Unauthorized financial evidence"
        not in answer.answer
    )

    check(
        "Legacy evidence excluded from answer",
        "Unverified legacy evidence"
        not in answer.answer
    )

check(
    "Global document lookup never called",
    not repo.get_document_by_id.called
    and not repo.list_documents.called
)

print("\n==============================")
print(f"Total tests : {passed + failed}")
print(f"Passed      : {passed}")
print(f"Failed      : {failed}")
print("==============================")

if failed:
    raise SystemExit(1)

print("ALL RESEARCH SECURITY TESTS PASSED!")