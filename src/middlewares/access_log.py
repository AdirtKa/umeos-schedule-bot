from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from src.logger import get_access_logger, get_error_logger


class AccessLogMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.access_logger = get_access_logger()
        self.error_logger = get_error_logger()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        update_id, event_type = self._get_event_details(event)
        self.access_logger.info("Incoming update | update_id=%s | type=%s", update_id, event_type)

        try:
            result = await handler(event, data)
        except Exception:
            self.error_logger.exception(
                "Unhandled update error | update_id=%s | type=%s",
                update_id,
                event_type,
            )
            raise

        self.access_logger.info("Handled update | update_id=%s | type=%s", update_id, event_type)
        return result

    @staticmethod
    def _get_event_details(event: TelegramObject) -> tuple[int | str, str]:
        if isinstance(event, Update):
            return event.update_id, event.event_type

        return "-", event.__class__.__name__
