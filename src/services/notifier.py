from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import date, datetime, time, timedelta
from html import escape
import logging
from typing import Any
from zoneinfo import ZoneInfo

from aiogram import Bot

from src.repositories.chat_settings import ChatSettingsRepository, ReminderChatSettings
from src.services.schedule_service import ScheduleService, ScheduleServiceError, TodaySchedule

logger = logging.getLogger(__name__)

MOSCOW_TZ = ZoneInfo("Europe/Moscow")


class NotifierService:
    def __init__(
        self,
        chat_settings_repository: ChatSettingsRepository,
        schedule_service: ScheduleService,
        now_factory: Callable[[], datetime] | None = None,
        check_interval_seconds: int = 60,
    ) -> None:
        self.chat_settings_repository = chat_settings_repository
        self.schedule_service = schedule_service
        self.now_factory = now_factory or self._moscow_now
        self.check_interval_seconds = check_interval_seconds

    async def set_reminder_hours(self, chat_id: int, hours_before: int) -> bool:
        return await asyncio.to_thread(
            self.chat_settings_repository.set_reminder_hours,
            chat_id,
            hours_before,
        )

    async def disable_reminders(self, chat_id: int) -> bool:
        return await asyncio.to_thread(self.chat_settings_repository.disable_reminders, chat_id)

    async def get_reminder_hours(self, chat_id: int) -> int | None:
        return await asyncio.to_thread(self.chat_settings_repository.get_reminder_hours, chat_id)

    async def run(self, bot: Bot) -> None:
        while True:
            await self.send_due_notifications(bot)
            await asyncio.sleep(self.check_interval_seconds)

    async def send_due_notifications(self, bot: Bot) -> None:
        now = self._get_now()
        target_date = now.date()
        chats = await asyncio.to_thread(self.chat_settings_repository.get_chats_with_reminders)

        for chat_settings in chats:
            if chat_settings.last_notified_date == target_date:
                continue

            try:
                await self._send_chat_notification_if_due(bot, chat_settings, now, target_date)
            except Exception:
                logger.exception("Notifier failed for chat %s", chat_settings.chat_id)

    async def _send_chat_notification_if_due(
        self,
        bot: Bot,
        chat_settings: ReminderChatSettings,
        now: datetime,
        target_date: date,
    ) -> None:
        try:
            today_schedule = await self.schedule_service.get_schedule_for_group_date(
                chat_settings.group_name,
                target_date,
            )
        except ScheduleServiceError:
            logger.exception("Failed to prepare reminder for chat %s", chat_settings.chat_id)
            return

        notification_time = self._get_notification_time(today_schedule, chat_settings)

        if notification_time is None:
            await self._mark_reminder_sent(chat_settings.chat_id, target_date)
            return

        if now < notification_time:
            return

        try:
            await bot.send_message(
                chat_id=chat_settings.chat_id,
                text=format_reminder(today_schedule, chat_settings.reminder_hours_before),
            )
        except Exception:
            logger.exception("Failed to send reminder to chat %s", chat_settings.chat_id)
            return

        await self._mark_reminder_sent(chat_settings.chat_id, target_date)

    async def _mark_reminder_sent(self, chat_id: int, target_date: date) -> None:
        await asyncio.to_thread(
            self.chat_settings_repository.mark_reminder_sent,
            chat_id,
            target_date,
        )

    @staticmethod
    def _get_notification_time(
        today_schedule: TodaySchedule,
        chat_settings: ReminderChatSettings,
    ) -> datetime | None:
        first_start_time = _get_first_course_start_time(today_schedule)

        if first_start_time is None:
            return None

        first_course_datetime = datetime.combine(
            today_schedule.target_date,
            first_start_time,
            tzinfo=MOSCOW_TZ,
        )

        return first_course_datetime - timedelta(hours=chat_settings.reminder_hours_before)

    @staticmethod
    def _moscow_now() -> datetime:
        return datetime.now(MOSCOW_TZ)

    def _get_now(self) -> datetime:
        now = self.now_factory()

        if now.tzinfo is None:
            return now.replace(tzinfo=MOSCOW_TZ)

        return now.astimezone(MOSCOW_TZ)


def format_reminder(today_schedule: TodaySchedule, hours_before: int) -> str:
    group_name = escape(today_schedule.group_name)
    formatted_date = today_schedule.target_date.strftime("%d.%m.%Y")
    starts = _format_course_starts(today_schedule.day)

    return (
        "<b>Напоминание о парах на сегодня</b>\n"
        f"Группа: <b>{group_name}</b>\n"
        f"Дата: {formatted_date} МСК\n"
        f"Напоминаю за {hours_before} ч.\n\n"
        f"{starts}"
    )


def _format_course_starts(day: dict[str, Any] | None) -> str:
    if day is None:
        return "Занятий на сегодня нет."

    courses = day.get("courses", [])

    if not courses:
        return "Занятий на сегодня нет."

    lines = []
    for course in courses:
        number = escape(str(course.get("number", "")))
        start_time = escape(str(course.get("start_time", "")))
        lines.append(f"{number} пара — {start_time}")

    return "\n".join(lines)


def _get_first_course_start_time(today_schedule: TodaySchedule) -> time | None:
    if today_schedule.day is None:
        return None

    course_times = [
        time.fromisoformat(course["start_time"])
        for course in today_schedule.day.get("courses", [])
        if course.get("start_time")
    ]

    if not course_times:
        return None

    return min(course_times)
