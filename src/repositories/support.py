from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import sqlite3


@dataclass(frozen=True)
class SupportTicket:
    user_id: int
    username: str | None
    full_name: str
    last_message: str
    status: str
    created_at: str
    updated_at: str


class SupportRepository:
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
                CREATE TABLE IF NOT EXISTS support_tickets (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT NOT NULL,
                    last_message TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def upsert_ticket(
        self,
        user_id: int,
        username: str | None,
        full_name: str,
        message_text: str,
    ) -> SupportTicket:
        now = datetime.now(UTC).isoformat()

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO support_tickets (
                    user_id,
                    username,
                    full_name,
                    last_message,
                    status,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id)
                DO UPDATE SET
                    username = excluded.username,
                    full_name = excluded.full_name,
                    last_message = excluded.last_message,
                    status = excluded.status,
                    updated_at = excluded.updated_at
                """,
                (user_id, username, full_name, message_text, "open", now, now),
            )

        ticket = self.get_ticket(user_id)

        if ticket is None:
            msg = f"Failed to save support ticket for user {user_id}"
            raise RuntimeError(msg)

        return ticket

    def get_ticket(self, user_id: int) -> SupportTicket | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT user_id, username, full_name, last_message, status, created_at, updated_at
                FROM support_tickets
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()

        if row is None:
            return None

        return self._map_ticket(row)

    def get_open_tickets(self, limit: int = 20) -> list[SupportTicket]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT user_id, username, full_name, last_message, status, created_at, updated_at
                FROM support_tickets
                WHERE status = ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                ("open", limit),
            ).fetchall()

        return [self._map_ticket(row) for row in rows]

    def close_ticket(self, user_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE support_tickets
                SET status = ?,
                    updated_at = ?
                WHERE user_id = ?
                """,
                ("closed", datetime.now(UTC).isoformat(), user_id),
            )

        return cursor.rowcount > 0

    @staticmethod
    def _map_ticket(row: tuple[int, str | None, str, str, str, str, str]) -> SupportTicket:
        return SupportTicket(
            user_id=row[0],
            username=row[1],
            full_name=row[2],
            last_message=row[3],
            status=row[4],
            created_at=row[5],
            updated_at=row[6],
        )
