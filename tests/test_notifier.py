from datetime import date, datetime
from pathlib import Path

import pytest

from src.parsers.schedule import ScheduleParser
from src.repositories.chat_settings import ChatSettingsRepository
from src.repositories.schedule import ScheduleRepository
from src.repositories.umeos import FilterType
from src.services.notifier import MOSCOW_TZ, NotifierService
from src.services.schedule_service import ScheduleService


class FakeBot:
    def __init__(self) -> None:
        self.messages: list[tuple[int, str]] = []

    async def send_message(self, chat_id: int, text: str) -> None:
        self.messages.append((chat_id, text))


class FakeUmeosRepository:
    def __init__(self, html: str) -> None:
        self.html = html

    def fetch_schedule(
        self,
        _filter_value: str,
        _filter_type: FilterType = FilterType.GROUP,
    ) -> str:
        return self.html


@pytest.fixture
def schedule_html() -> str:
    fixture_path = Path(__file__).parent / "fixtures" / "schedule.html"
    return fixture_path.read_text(encoding="utf-8")


def create_notifier(
    tmp_path: Path,
    schedule_html: str,
    now: datetime,
) -> tuple[NotifierService, FakeBot, ChatSettingsRepository]:
    chat_settings_repository = ChatSettingsRepository(tmp_path / "bot.db")
    schedule_service = ScheduleService(
        chat_settings_repository=chat_settings_repository,
        schedule_repository=ScheduleRepository(tmp_path / "schedules"),
        schedule_parser=ScheduleParser(),
        umeos_repository=FakeUmeosRepository(schedule_html),
        today_factory=lambda: date(2026, 10, 5),
    )
    notifier_service = NotifierService(
        chat_settings_repository=chat_settings_repository,
        schedule_service=schedule_service,
        now_factory=lambda: now,
    )

    return notifier_service, FakeBot(), chat_settings_repository


async def test_notifier_sends_due_reminder_once_per_day(
    tmp_path: Path,
    schedule_html: str,
) -> None:
    notifier_service, bot, chat_settings_repository = create_notifier(
        tmp_path,
        schedule_html,
        datetime(2026, 10, 5, 17, 10, tzinfo=MOSCOW_TZ),
    )
    chat_settings_repository.set_group(123, "ОэУИТм-М05-26-1")
    chat_settings_repository.set_reminder_hours(123, 2)

    await notifier_service.send_due_notifications(bot)
    await notifier_service.send_due_notifications(bot)

    assert bot.messages == [
        (
            123,
            (
                "<b>Напоминание о парах на сегодня</b>\n"
                "Группа: <b>ОэУИТм-М05-26-1</b>\n"
                "Дата: 05.10.2026 МСК\n"
                "Напоминаю за 2 ч.\n\n"
                "7 пара — 19:10\n"
                "8 пара — 20:45"
            ),
        )
    ]


async def test_notifier_waits_until_reminder_time(
    tmp_path: Path,
    schedule_html: str,
) -> None:
    notifier_service, bot, chat_settings_repository = create_notifier(
        tmp_path,
        schedule_html,
        datetime(2026, 10, 5, 17, 9, tzinfo=MOSCOW_TZ),
    )
    chat_settings_repository.set_group(123, "ОэУИТм-М05-26-1")
    chat_settings_repository.set_reminder_hours(123, 2)

    await notifier_service.send_due_notifications(bot)

    assert bot.messages == []
