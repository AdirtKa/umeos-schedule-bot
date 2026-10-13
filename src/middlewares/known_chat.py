from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject, Update

from src.repositories.chat_settings import ChatSettingsRepository


class KnownChatMiddleware(BaseMiddleware):
    def __init__(self, chat_settings_repository: ChatSettingsRepository) -> None:
        self.chat_settings_repository = chat_settings_repository

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        message = self._get_message(event)

        if message is not None:
            await self._record_chat(message)

        return await handler(event, data)

    async def _record_chat(self, message: Message) -> None:
        chat = message.chat
        user = message.from_user

        await asyncio.to_thread(
            self.chat_settings_repository.record_known_chat,
            chat.id,
            str(chat.type),
            getattr(chat, "title", None),
            getattr(chat, "username", None) or (user.username if user else None),
            (user.first_name if user else getattr(chat, "first_name", None)),
            (user.last_name if user else getattr(chat, "last_name", None)),
        )

    @staticmethod
    def _get_message(event: TelegramObject) -> Message | None:
        if isinstance(event, Message):
            return event

        if not isinstance(event, Update):
            return None

        return (
            event.message or event.edited_message or event.channel_post or event.edited_channel_post
        )
