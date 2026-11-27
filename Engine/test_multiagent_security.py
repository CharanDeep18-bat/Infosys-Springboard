import httpx
from getpass import getpass

BASE_URL = "http://localhost:8000"

token_a = getpass("Enter Account A access token: ")
token_b = getpass("Enter Account B access token: ")

doc_a = input("Account A document ID: ").strip()
doc_b = input("Account B document ID: ").strip()

session_a = input("Account A session ID: ").strip()
session_b = input("Account B session ID: ").strip()

passed = 0
failed = 0


def test(name, method, path, expected, token=None, body=None):
    global passed, failed

    headers = {}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = httpx.request(
            method,
            BASE_URL + path,
            headers=headers,
            json=body,
            timeout=60
        )

        expected_codes = (
            expected if isinstance(expected, tuple)
            else (expected,)
        )

        if response.status_code in expected_codes:
            passed += 1
            print(f"[PASS] {name}: {response.status_code}")
        else:
            failed += 1
            print(
                f"[FAIL] {name}: "
                f"Expected {expected}, "
                f"Received {response.status_code}"
            )

    except httpx.RequestError as exc:
        failed += 1
        print(f"[FAIL] {name}: {exc}")


print("\n--- Authentication verification ---")

test(
    "Account A authentication",
    "GET", "/auth/me", 200, token_a
)

test(
    "Account B authentication",
    "GET", "/auth/me", 200, token_b
)


print("\n--- Extraction Agent ---")

test(
    "Cross-user extraction",
    "GET",
    f"/documents/{doc_b}/extraction",
    404, token_a
)

test(
    "Unauthenticated extraction",
    "GET",
    f"/documents/{doc_a}/extraction",
    401
)


print("\n--- Red Flag Agent ---")

test(
    "Owned red flags",
    "GET",
    f"/documents/{doc_a}/red-flags",
    200, token_a
)

test(
    "Cross-user red flags",
    "GET",
    f"/documents/{doc_b}/red-flags",
    404, token_a
)

test(
    "Unauthenticated red flags",
    "GET",
    f"/documents/{doc_a}/red-flags",
    401
)


print("\n--- Research Agent ---")

test(
    "Cross-user research",
    "POST", "/research/query",
    404, token_a,
    {
        "question": "Summarize revenue",
        "document_ids": [doc_b]
    }
)

test(
    "Mixed-owner research",
    "POST", "/research/query",
    404, token_a,
    {
        "question": "Compare revenue",
        "document_ids": [doc_a, doc_b]
    }
)

test(
    "Cross-user session research",
    "POST",
    f"/research/sessions/{session_b}/query",
    404, token_a,
    {"question": "Summarize revenue"}
)

test(
    "Owned conversation history",
    "GET",
    f"/research/sessions/{session_a}/messages",
    200, token_a
)

test(
    "Cross-user conversation history",
    "GET",
    f"/research/sessions/{session_b}/messages",
    404, token_a
)

test(
    "Unauthenticated research",
    "POST", "/research/query",
    401, None,
    {
        "question": "Summarize revenue",
        "document_ids": [doc_a]
    }
)


print("\n--- Comparison Agent ---")

test(
    "Mixed-owner comparison",
    "POST", "/comparison",
    404, token_a,
    {"document_ids": [doc_a, doc_b]}
)

test(
    "Duplicate document comparison",
    "POST", "/comparison",
    400, token_a,
    {"document_ids": [doc_a, doc_a]}
)

test(
    "Unauthenticated comparison",
    "POST", "/comparison",
    401, None,
    {"document_ids": [doc_a, doc_b]}
)


print("\n--- Report Agent ---")

test(
    "Cross-user report generation",
    "POST", "/reports/generate",
    404, token_a,
    {"document_id": doc_b}
)

test(
    "Unauthenticated report generation",
    "POST", "/reports/generate",
    401, None,
    {"document_id": doc_a}
)


print("\n--- Workflow Processing ---")

test(
    "Owned document processing",
    "POST",
    f"/documents/{doc_a}/process",
    503, token_a
)

test(
    "Cross-user processing",
    "POST",
    f"/documents/{doc_b}/process",
    404, token_a
)

test(
    "Alternative processing endpoint",
    "POST", "/documents/process",
    404, token_a,
    {"document_id": doc_b}
)

test(
    "Unauthorized session context",
    "POST",
    f"/documents/{doc_a}/process",
    404, token_a,
    {
        "document_id": doc_a,
        "session_id": session_b
    }
)

test(
    "Unauthenticated processing",
    "POST",
    f"/documents/{doc_a}/process",
    401
)


print("\n--- Reverse Account Isolation ---")

test(
    "Account B owned red flags",
    "GET",
    f"/documents/{doc_b}/red-flags",
    200, token_b
)

test(
    "Account B accessing Account A document",
    "GET",
    f"/documents/{doc_a}/red-flags",
    404, token_b
)

test(
    "Account B accessing Account A session",
    "GET",
    f"/research/sessions/{session_a}/messages",
    404, token_b
)


print("\n==============================")
print(f"Total tests : {passed + failed}")
print(f"Passed      : {passed}")
print(f"Failed      : {failed}")
print("==============================")

if failed:
    raise SystemExit(1)

print("All multi-agent authorization tests passed!")