import sqlite3
import re
from app.config import get_settings

db_path = str(get_settings().sqlite_db_path)

conn = sqlite3.connect(db_path)
conn.execute("PRAGMA foreign_keys = OFF")

try:
    conn.execute("BEGIN IMMEDIATE")

    for table in ["ai_documents", "documents"]:

        schema = conn.execute(
            """
            SELECT sql FROM sqlite_master
            WHERE type = 'table' AND name = ?
            """,
            (table,)
        ).fetchone()[0]

        new_schema, changed = re.subn(
            r"sha256\s+TEXT\s+NOT\s+NULL\s+UNIQUE",
            "sha256 TEXT NOT NULL",
            schema,
            flags=re.IGNORECASE
        )

        if not changed:
            print(f"{table}: No migration required")
            continue

        objects = conn.execute(
            """
            SELECT sql FROM sqlite_master
            WHERE tbl_name = ?
            AND type IN ('index', 'trigger')
            AND sql IS NOT NULL
            """,
            (table,)
        ).fetchall()

        new_table = table + "_new"

        new_schema = re.sub(
            r"^CREATE TABLE\s+(?:IF NOT EXISTS\s+)?"
            r'["`\[]?' + table + r'["`\]]?',
            f"CREATE TABLE {new_table}",
            new_schema,
            count=1,
            flags=re.IGNORECASE
        )

        conn.execute(new_schema)

        columns = [
            row[1]
            for row in conn.execute(
                f"PRAGMA table_info({table})"
            )
        ]

        column_names = ", ".join(
            f'"{c}"' for c in columns
        )

        conn.execute(
            f"""
            INSERT INTO {new_table} ({column_names})
            SELECT {column_names} FROM {table}
            """
        )

        conn.execute(f"DROP TABLE {table}")

        conn.execute(
            f"ALTER TABLE {new_table} RENAME TO {table}"
        )

        for (sql,) in objects:
            conn.execute(sql)

        print(f"{table}: Migration successful")

    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
        idx_ai_documents_user_sha256
        ON ai_documents(user_id, sha256)
        """
    )

    violations = conn.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    if violations:
        raise RuntimeError(
            f"Foreign key violations: {violations}"
        )

    conn.commit()

    print("Foreign key validation: PASSED")
    print("Database migration completed!")

except Exception:
    conn.rollback()
    raise

finally:
    conn.execute("PRAGMA foreign_keys = ON")
    conn.close()