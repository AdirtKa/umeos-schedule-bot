from __future__ import annotations

import asyncio

from aiogram.types import User

from src.repositories.support import SupportRepository, SupportTicket


class SupportService:
    def __init__(self, support_repository: SupportRepository) -> None:
        self.support_repository = support_repository

    async def open_ticket(self, user: User, message_text: str) -> SupportTicket:
        return await asyncio.to_thread(
            self.support_repository.upsert_ticket,
            user.id,
            user.username,
            _format_full_name(user),
            message_text,
        )

    async def get_ticket(self, user_id: int) -> SupportTicket | None:
        return await asyncio.to_thread(self.support_repository.get_ticket, user_id)

    async def get_open_tickets(self) -> list[SupportTicket]:
        return await asyncio.to_thread(self.support_repository.get_open_tickets)

    async def close_ticket(self, user_id: int) -> bool:
        return await asyncio.to_thread(self.support_repository.close_ticket, user_id)


def _format_full_name(user: User) -> str:
    names = [user.first_name, user.last_name]
    return " ".join(name for name in names if name) or str(user.id)
