from app.infrastructure.database import (
    get_database_repository,
    SQLiteRepository,
)
from app.schemas.research import GeneratedReport


class ReportRepository:

    def __init__(self, repository=None):
        self.repo = (
            repository
            if repository is not None
            else get_database_repository()
        )

        if not isinstance(self.repo, SQLiteRepository):
            raise RuntimeError(
                "Report persistence requires SQLite"
            )

        with self.repo._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_saved_reports (
                    report_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    report_json TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_saved_reports_user
                ON ai_saved_reports(user_id)
            """)

    def save_report(self, user_id, report):
        with self.repo._get_connection() as conn:
            conn.execute("""
                INSERT INTO ai_saved_reports
                (report_id, user_id, generated_at, report_json)
                VALUES (?, ?, ?, ?)
            """, (
                report.report_id,
                user_id,
                report.generated_at,
                report.model_dump_json()
            ))

        return report

    def list_reports(self, user_id):
        with self.repo._get_connection() as conn:
            rows = conn.execute("""
                SELECT report_json
                FROM ai_saved_reports
                WHERE user_id = ?
                ORDER BY generated_at DESC
            """, (user_id,)).fetchall()

        return [
            GeneratedReport.model_validate_json(
                row["report_json"]
            )
            for row in rows
        ]

    def get_report(self, report_id, user_id):
        with self.repo._get_connection() as conn:
            row = conn.execute("""
                SELECT report_json
                FROM ai_saved_reports
                WHERE report_id = ? AND user_id = ?
            """, (report_id, user_id)).fetchone()

        if row is None:
            return None

        return GeneratedReport.model_validate_json(
            row["report_json"]
        )

    def rename_report(self, report_id, user_id, title):
        report = self.get_report(report_id, user_id)

        if report is None:
            return None

        report.title = title

        with self.repo._get_connection() as conn:
            cursor = conn.execute("""
                UPDATE ai_saved_reports
                SET report_json = ?
                WHERE report_id = ? AND user_id = ?
            """, (
                report.model_dump_json(),
                report_id,
                user_id
            ))

            if cursor.rowcount == 0:
                return None

        return report

    def delete_report(self, report_id, user_id):
        with self.repo._get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM ai_saved_reports
                WHERE report_id = ? AND user_id = ?
            """, (report_id, user_id))

            return cursor.rowcount > 0