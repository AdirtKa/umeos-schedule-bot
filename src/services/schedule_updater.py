from collections.abc import Iterator
import logging

from src.parsers.schedule import ScheduleParser
from src.repositories.chat_settings import ChatSettingsRepository
from src.repositories.schedule import ScheduleRepository
from src.repositories.umeos import FilterType, UmeosRepository

logger = logging.getLogger(__name__)


class ScheduleUpdater:
    def __init__(
        self,
        chat_settings_repository: ChatSettingsRepository,
        schedule_repository: ScheduleRepository,
        schedule_parser: ScheduleParser,
    ) -> None:
        self.chat_settings_repository = chat_settings_repository
        self.schedule_repository = schedule_repository
        self.schedule_parser = schedule_parser
        self.umeos_repository = UmeosRepository()

    def fetch_schedules(self) -> Iterator[tuple[str, str]]:
        groups = self.chat_settings_repository.get_distinct_groups()

        for group in groups:
            try:
                html = self.umeos_repository.fetch_schedule(
                    group,
                    FilterType.GROUP,
                )
            except Exception:
                logger.exception("Failed to fetch schedule for group %s", group)
                continue

            yield group, html

    def run(self) -> None:
        for group, html in self.fetch_schedules():
            try:
                schedule = self.schedule_parser.parse_schedule(html)

                self.schedule_repository.write(
                    group,
                    schedule,
                )
                logger.info("Schedule updated for group %s", group)
            except Exception:
                logger.exception("Failed to parse or save schedule for group %s", group)
