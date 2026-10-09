from dataclasses import dataclass
from datetime import date
from pathlib import Path
import sqlite3


@dataclass(frozen=True)
class ReminderChatSettings:
    chat_id: int
    group_name: str
    reminder_hours_before: int
    last_notified_date: date | None


class ChatSettingsRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_settings (
                    chat_id INTEGER PRIMARY KEY,
                    group_name TEXT NOT NULL,
                    reminder_hours_before INTEGER,
                    last_notified_date TEXT
                )
                """
            )
            self._ensure_column(connection, "reminder_hours_before", "INTEGER")
            self._ensure_column(connection, "last_notified_date", "TEXT")

    @staticmethod
    def _ensure_column(connection: sqlite3.Connection, name: str, definition: str) -> None:
        rows = connection.execute("PRAGMA table_info(chat_settings)").fetchall()
        column_names = {row[1] for row in rows}

        if name not in column_names:
            connection.execute(f"ALTER TABLE chat_settings ADD COLUMN {name} {definition}")

    def set_group(self, chat_id: int, group_name: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO chat_settings (chat_id, group_name)
                VALUES (?, ?)
                ON CONFLICT(chat_id)
                DO UPDATE SET group_name = excluded.group_name
                """,
                (chat_id, group_name),
            )

    def get_group(self, chat_id: int) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT group_name
                FROM chat_settings
                WHERE chat_id = ?
                """,
                (chat_id,),
            ).fetchone()

        if row is None:
            return None

        return row[0]

    def get_distinct_groups(self) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT group_name
                FROM chat_settings
                ORDER BY group_name
                """
            ).fetchall()

        return [row[0] for row in rows]

    def set_reminder_hours(self, chat_id: int, hours_before: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE chat_settings
                SET reminder_hours_before = ?
                WHERE chat_id = ?
                """,
                (hours_before, chat_id),
            )

        return cursor.rowcount > 0

    def disable_reminders(self, chat_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE chat_settings
                SET reminder_hours_before = NULL
                WHERE chat_id = ?
                """,
                (chat_id,),
            )

        return cursor.rowcount > 0

    def get_reminder_hours(self, chat_id: int) -> int | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT reminder_hours_before
                FROM chat_settings
                WHERE chat_id = ?
                """,
                (chat_id,),
            ).fetchone()

        if row is None:
            return None

        return row[0]

    def get_chats_with_reminders(self) -> list[ReminderChatSettings]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT chat_id, group_name, reminder_hours_before, last_notified_date
                FROM chat_settings
                WHERE reminder_hours_before IS NOT NULL
                ORDER BY chat_id
                """
            ).fetchall()

        return [
            ReminderChatSettings(
                chat_id=row[0],
                group_name=row[1],
                reminder_hours_before=row[2],
                last_notified_date=date.fromisoformat(row[3]) if row[3] else None,
            )
            for row in rows
        ]

    def mark_reminder_sent(self, chat_id: int, target_date: date) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE chat_settings
                SET last_notified_date = ?
                WHERE chat_id = ?
                """,
                (target_date.isoformat(), chat_id),
            )

    def delete_chat(self, chat_id: int) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                DELETE FROM chat_settings
                WHERE chat_id = ?
                """,
                (chat_id,),
            )
