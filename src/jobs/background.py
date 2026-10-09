import asyncio
from collections.abc import Callable
from contextlib import suppress
from datetime import datetime
import logging

from aiogram import Bot

from src.jobs.schedule import MOSCOW_TZ, seconds_until_next_daily_run
from src.services.notifier import NotifierService
from src.services.schedule_updater import ScheduleUpdater

logger = logging.getLogger(__name__)


class BackgroundJobs:
    def __init__(
        self,
        bot: Bot,
        notifier_service: NotifierService,
        schedule_updater: ScheduleUpdater,
        now_factory: Callable[[], datetime] | None = None,
        notifier_interval_seconds: int = 60,
    ) -> None:
        self.bot = bot
        self.notifier_service = notifier_service
        self.schedule_updater = schedule_updater
        self.now_factory = now_factory or self._moscow_now
        self.notifier_interval_seconds = notifier_interval_seconds
        self._tasks: list[asyncio.Task[None]] = []

    def start(self) -> None:
        self._tasks = [
            asyncio.create_task(self._run_notifier_job(), name="notifier-job"),
            asyncio.create_task(self._run_schedule_updater_job(), name="schedule-updater-job"),
        ]

    async def stop(self) -> None:
        for task in self._tasks:
            task.cancel()

        for task in self._tasks:
            with suppress(asyncio.CancelledError):
                await task

        self._tasks.clear()

    async def _run_notifier_job(self) -> None:
        while True:
            try:
                await self.notifier_service.send_due_notifications(self.bot)
            except Exception:
                logger.exception("Notifier job failed")

            await asyncio.sleep(self.notifier_interval_seconds)

    async def _run_schedule_updater_job(self) -> None:
        while True:
            delay = seconds_until_next_daily_run(self.now_factory())
            logger.info("Schedule updater job sleeps %.0f seconds until next 00:00 MSK", delay)

            await asyncio.sleep(delay)

            try:
                await asyncio.to_thread(self.schedule_updater.run)
            except Exception:
                logger.exception("Schedule updater job failed")

    @staticmethod
    def _moscow_now() -> datetime:
        return datetime.now(MOSCOW_TZ)
