import sqlite3
from app.config import get_settings

conn = sqlite3.connect(get_settings().sqlite_db_path)

tables = ["workspaces", "research_sessions", "ai_documents"]

for table in tables:
    print(f"\nTable: {table}")

    columns = conn.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    for column in columns:
        print(column[1], "-", column[2])

conn.close()