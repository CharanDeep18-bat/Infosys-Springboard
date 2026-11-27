import sqlite3
from app.config import get_settings

conn = sqlite3.connect(str(get_settings().sqlite_db_path))

queries = {
    "Document ownership": """
        SELECT d.document_id
        FROM ai_documents d
        LEFT JOIN workspaces w
        ON d.workspace_id = w.workspace_id
        WHERE d.user_id IS NOT NULL
        AND (
            w.user_id IS NULL
            OR d.user_id != w.user_id
        )
    """,

    "Session ownership": """
        SELECT s.session_id
        FROM research_sessions s
        LEFT JOIN workspaces w
        ON s.workspace_id = w.workspace_id
        WHERE s.user_id IS NOT NULL
        AND (
            w.user_id IS NULL
            OR s.user_id != w.user_id
        )
    """,

    "Session-document ownership": """
        SELECT sd.session_id, sd.document_id
        FROM session_documents sd
        JOIN research_sessions s
        ON sd.session_id = s.session_id
        LEFT JOIN ai_documents d
        ON sd.document_id = d.document_id
        WHERE s.user_id IS NOT NULL
        AND (
            d.user_id IS NULL
            OR s.user_id != d.user_id
            OR s.workspace_id != d.workspace_id
        )
    """,

    "Same-user duplicate hashes": """
        SELECT user_id, sha256, COUNT(*)
        FROM ai_documents
        WHERE user_id IS NOT NULL
        GROUP BY user_id, sha256
        HAVING COUNT(*) > 1
    """
}

passed = True

for name, query in queries.items():
    rows = conn.execute(query).fetchall()

    if rows:
        passed = False
        print(f"{name}: FAILED")
        print(rows)
    else:
        print(f"{name}: PASSED")

violations = conn.execute(
    "PRAGMA foreign_key_check"
).fetchall()

if violations:
    passed = False
    print("Foreign key integrity: FAILED")
    print(violations)
else:
    print("Foreign key integrity: PASSED")

conn.close()

if passed:
    print("\nAll database isolation checks passed!")
else:
    raise SystemExit("Isolation checks failed")