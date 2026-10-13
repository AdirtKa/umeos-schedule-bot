from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
import sqlite3


@dataclass(frozen=True)
class ReminderChatSettings:
    chat_id: int
    group_name: str
    reminder_minutes_before: int
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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_reminders (
                    chat_id INTEGER NOT NULL,
                    reminder_minutes_before INTEGER NOT NULL,
                    last_notified_date TEXT,
                    PRIMARY KEY (chat_id, reminder_minutes_before)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS known_chats (
                    chat_id INTEGER PRIMARY KEY,
                    chat_type TEXT NOT NULL,
                    title TEXT,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    updated_at TEXT NOT NULL
                )
                """
            )
            self._migrate_legacy_reminders(connection)
            self._migrate_known_chats(connection)

    @staticmethod
    def _ensure_column(connection: sqlite3.Connection, name: str, definition: str) -> None:
        rows = connection.execute("PRAGMA table_info(chat_settings)").fetchall()
        column_names = {row[1] for row in rows}

        if name not in column_names:
            connection.execute(f"ALTER TABLE chat_settings ADD COLUMN {name} {definition}")

    @staticmethod
    def _migrate_legacy_reminders(connection: sqlite3.Connection) -> None:
        rows = connection.execute(
            """
            SELECT chat_id, reminder_hours_before, last_notified_date
            FROM chat_settings
            WHERE reminder_hours_before IS NOT NULL
            """
        ).fetchall()

        for chat_id, hours_before, last_notified_date in rows:
            connection.execute(
                """
                INSERT OR IGNORE INTO chat_reminders (
                    chat_id,
                    reminder_minutes_before,
                    last_notified_date
                )
                VALUES (?, ?, ?)
                """,
                (chat_id, int(hours_before) * 60, last_notified_date),
            )

    @staticmethod
    def _migrate_known_chats(connection: sqlite3.Connection) -> None:
        now = datetime.now(UTC).isoformat()
        rows = connection.execute(
            """
            SELECT chat_id
            FROM chat_settings
            """
        ).fetchall()

        for (chat_id,) in rows:
            connection.execute(
                """
                INSERT OR IGNORE INTO known_chats (chat_id, chat_type, updated_at)
                VALUES (?, ?, ?)
                """,
                (chat_id, "unknown", now),
            )

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
        return self.set_reminder_minutes(chat_id, [hours_before * 60])

    def set_reminder_minutes(self, chat_id: int, reminder_minutes: Iterable[int]) -> bool:
        normalized_minutes = self._normalize_reminder_minutes(reminder_minutes)

        with self._connect() as connection:
            chat_exists = self._chat_exists(connection, chat_id)

            if not chat_exists:
                return False

            existing_rows = connection.execute(
                """
                SELECT reminder_minutes_before, last_notified_date
                FROM chat_reminders
                WHERE chat_id = ?
                """,
                (chat_id,),
            ).fetchall()
            existing_dates = {row[0]: row[1] for row in existing_rows}

            connection.execute(
                """
                DELETE FROM chat_reminders
                WHERE chat_id = ?
                """,
                (chat_id,),
            )
            connection.executemany(
                """
                INSERT INTO chat_reminders (
                    chat_id,
                    reminder_minutes_before,
                    last_notified_date
                )
                VALUES (?, ?, ?)
                """,
                [
                    (chat_id, minutes_before, existing_dates.get(minutes_before))
                    for minutes_before in normalized_minutes
                ],
            )
            connection.execute(
                """
                UPDATE chat_settings
                SET reminder_hours_before = NULL,
                    last_notified_date = NULL
                WHERE chat_id = ?
                """,
                (chat_id,),
            )

        return True

    def add_reminder_minutes(self, chat_id: int, reminder_minutes: Iterable[int]) -> bool:
        normalized_minutes = self._normalize_reminder_minutes(reminder_minutes)

        with self._connect() as connection:
            if not self._chat_exists(connection, chat_id):
                return False

            connection.executemany(
                """
                INSERT OR IGNORE INTO chat_reminders (
                    chat_id,
                    reminder_minutes_before,
                    last_notified_date
                )
                VALUES (?, ?, NULL)
                """,
                [(chat_id, minutes_before) for minutes_before in normalized_minutes],
            )

        return True

    def remove_reminder_minutes(self, chat_id: int, reminder_minutes: Iterable[int]) -> bool:
        normalized_minutes = self._normalize_reminder_minutes(reminder_minutes)

        with self._connect() as connection:
            if not self._chat_exists(connection, chat_id):
                return False

            connection.executemany(
                """
                DELETE FROM chat_reminders
                WHERE chat_id = ? AND reminder_minutes_before = ?
                """,
                [(chat_id, minutes_before) for minutes_before in normalized_minutes],
            )

        return True

    def disable_reminders(self, chat_id: int) -> bool:
        with self._connect() as connection:
            if not self._chat_exists(connection, chat_id):
                return False

            connection.execute(
                """
                DELETE FROM chat_reminders
                WHERE chat_id = ?
                """,
                (chat_id,),
            )
            connection.execute(
                """
                UPDATE chat_settings
                SET reminder_hours_before = NULL,
                    last_notified_date = NULL
                WHERE chat_id = ?
                """,
                (chat_id,),
            )

        return True

    def get_reminder_hours(self, chat_id: int) -> int | None:
        reminder_minutes = self.get_reminder_minutes(chat_id)

        if len(reminder_minutes) != 1:
            return None

        minutes_before = reminder_minutes[0]

        if minutes_before % 60 != 0:
            return None

        return minutes_before // 60

    def get_reminder_minutes(self, chat_id: int) -> list[int]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT reminder_minutes_before
                FROM chat_reminders
                WHERE chat_id = ?
                ORDER BY reminder_minutes_before DESC
                """,
                (chat_id,),
            ).fetchall()

        return [row[0] for row in rows]

    def get_chats_with_reminders(self) -> list[ReminderChatSettings]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    chat_settings.chat_id,
                    chat_settings.group_name,
                    chat_reminders.reminder_minutes_before,
                    chat_reminders.last_notified_date
                FROM chat_reminders
                INNER JOIN chat_settings
                    ON chat_settings.chat_id = chat_reminders.chat_id
                ORDER BY chat_settings.chat_id, chat_reminders.reminder_minutes_before DESC
                """
            ).fetchall()

        return [
            ReminderChatSettings(
                chat_id=row[0],
                group_name=row[1],
                reminder_minutes_before=row[2],
                last_notified_date=date.fromisoformat(row[3]) if row[3] else None,
            )
            for row in rows
        ]

    def mark_reminder_sent(
        self,
        chat_id: int,
        reminder_minutes_before: int,
        target_date: date,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE chat_reminders
                SET last_notified_date = ?
                WHERE chat_id = ? AND reminder_minutes_before = ?
                """,
                (target_date.isoformat(), chat_id, reminder_minutes_before),
            )

    def record_known_chat(
        self,
        chat_id: int,
        chat_type: str,
        title: str | None = None,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO known_chats (
                    chat_id,
                    chat_type,
                    title,
                    username,
                    first_name,
                    last_name,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(chat_id)
                DO UPDATE SET
                    chat_type = excluded.chat_type,
                    title = excluded.title,
                    username = excluded.username,
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    updated_at = excluded.updated_at
                """,
                (
                    chat_id,
                    chat_type,
                    title,
                    username,
                    first_name,
                    last_name,
                    datetime.now(UTC).isoformat(),
                ),
            )

    def get_known_chat_ids(self) -> list[int]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT chat_id
                FROM known_chats
                UNION
                SELECT chat_id
                FROM chat_settings
                ORDER BY chat_id
                """
            ).fetchall()

        return [row[0] for row in rows]

    def delete_chat(self, chat_id: int) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                DELETE FROM chat_reminders
                WHERE chat_id = ?
                """,
                (chat_id,),
            )
            connection.execute(
                """
                DELETE FROM chat_settings
                WHERE chat_id = ?
                """,
                (chat_id,),
            )

    @staticmethod
    def _chat_exists(connection: sqlite3.Connection, chat_id: int) -> bool:
        row = connection.execute(
            """
            SELECT 1
            FROM chat_settings
            WHERE chat_id = ?
            """,
            (chat_id,),
        ).fetchone()

        return row is not None

    @staticmethod
    def _normalize_reminder_minutes(reminder_minutes: Iterable[int]) -> list[int]:
        return sorted({int(minutes_before) for minutes_before in reminder_minutes}, reverse=True)
