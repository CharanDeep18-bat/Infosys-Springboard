import sqlite3
from app.config import get_settings

conn = sqlite3.connect(
    str(get_settings().sqlite_db_path)
)

rows = conn.execute(
    """
    SELECT document_id, filename, user_id, workspace_id
    FROM ai_documents
    WHERE user_id IS NOT NULL
    ORDER BY created_at DESC
    """
).fetchall()

for row in rows:
    print(row)

conn.close()