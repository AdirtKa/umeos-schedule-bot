from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
import logging
from typing import Any, Protocol

from src.parsers.schedule import ScheduleParser
from src.repositories.chat_settings import ChatSettingsRepository
from src.repositories.schedule import ScheduleRepository
from src.repositories.umeos import FilterType, UmeosRepository

logger = logging.getLogger(__name__)


class ScheduleServiceError(Exception):
    pass


class GroupNotSetError(ScheduleServiceError):
    pass


class ScheduleFetchError(ScheduleServiceError):
    pass


class ScheduleNotFoundError(ScheduleServiceError):
    pass


class ScheduleSource(Protocol):
    def fetch_schedule(
        self,
        filter_value: str,
        filter_type: FilterType = FilterType.GROUP,
    ) -> str: ...


@dataclass(frozen=True)
class TodaySchedule:
    group_name: str
    target_date: date
    day: dict[str, Any] | None


class ScheduleService:
    def __init__(
        self,
        chat_settings_repository: ChatSettingsRepository,
        schedule_repository: ScheduleRepository,
        schedule_parser: ScheduleParser,
        umeos_repository: ScheduleSource | None = None,
        today_factory: Callable[[], date] = date.today,
    ) -> None:
        self.chat_settings_repository = chat_settings_repository
        self.schedule_repository = schedule_repository
        self.schedule_parser = schedule_parser
        self.umeos_repository = umeos_repository or UmeosRepository()
        self.today_factory = today_factory

    async def set_group(self, chat_id: int, group_name: str) -> str:
        normalized_group_name = self._normalize_group_name(group_name)

        if not normalized_group_name:
            msg = "Group name is empty"
            raise ValueError(msg)

        await asyncio.to_thread(self._fetch_parse_and_save, normalized_group_name)
        await asyncio.to_thread(
            self.chat_settings_repository.set_group,
            chat_id,
            normalized_group_name,
        )

        return normalized_group_name

    async def get_group(self, chat_id: int) -> str | None:
        return await asyncio.to_thread(self.chat_settings_repository.get_group, chat_id)

    async def get_today_schedule(self, chat_id: int) -> TodaySchedule:
        target_date = self.today_factory()
        group_name = await self.get_group(chat_id)

        if group_name is None:
            raise GroupNotSetError

        return await self.get_schedule_for_group_date(group_name, target_date)

    async def get_schedule_for_group_date(
        self,
        group_name: str,
        target_date: date,
    ) -> TodaySchedule:
        schedule = await asyncio.to_thread(self._get_schedule_for_date, group_name, target_date)
        day = self._find_day(schedule, target_date)

        return TodaySchedule(
            group_name=group_name,
            target_date=target_date,
            day=day,
        )

    def _get_schedule_for_date(self, group_name: str, target_date: date) -> dict[str, Any]:
        cached_schedule = self.schedule_repository.read(group_name)

        if cached_schedule is not None and self._covers_date(cached_schedule, target_date):
            return cached_schedule

        return self._fetch_parse_and_save(group_name)

    def _fetch_parse_and_save(self, group_name: str) -> dict[str, Any]:
        try:
            html = self.umeos_repository.fetch_schedule(group_name, FilterType.GROUP)
        except Exception as exc:
            msg = f"Failed to fetch schedule for group {group_name}"
            raise ScheduleFetchError(msg) from exc

        try:
            schedule = self.schedule_parser.parse_schedule(html)
        except Exception as exc:
            msg = f"Failed to parse schedule for group {group_name}"
            raise ScheduleFetchError(msg) from exc

        if not schedule.get("weeks"):
            msg = f"Schedule not found for group {group_name}"
            raise ScheduleNotFoundError(msg)

        self.schedule_repository.write(group_name, schedule)
        logger.info("Schedule cached for group %s", group_name)

        return schedule

    @staticmethod
    def _normalize_group_name(group_name: str) -> str:
        return " ".join(group_name.split())

    @staticmethod
    def _covers_date(schedule: dict[str, Any], target_date: date) -> bool:
        for week in schedule.get("weeks", {}).values():
            start_date = date.fromisoformat(week["start_date"])
            end_date = date.fromisoformat(week["end_date"])

            if start_date <= target_date <= end_date:
                return True

        return False

    @staticmethod
    def _find_day(schedule: dict[str, Any], target_date: date) -> dict[str, Any] | None:
        target_date_iso = target_date.isoformat()

        for week in schedule.get("weeks", {}).values():
            for day in week.get("days", []):
                if day["date"] == target_date_iso:
                    return day

        return None
