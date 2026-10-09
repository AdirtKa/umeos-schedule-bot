from datetime import date
from pathlib import Path

import pytest

from src.parsers.schedule import ScheduleParser
from src.repositories.chat_settings import ChatSettingsRepository
from src.repositories.schedule import ScheduleRepository
from src.repositories.umeos import FilterType
from src.services.schedule_service import GroupNotSetError, ScheduleService


class FakeUmeosRepository:
    def __init__(self, html: str) -> None:
        self.html = html
        self.calls: list[tuple[str, FilterType]] = []

    def fetch_schedule(
        self,
        filter_value: str,
        filter_type: FilterType = FilterType.GROUP,
    ) -> str:
        self.calls.append((filter_value, filter_type))
        return self.html


@pytest.fixture
def schedule_html() -> str:
    fixture_path = Path(__file__).parent / "fixtures" / "schedule.html"
    return fixture_path.read_text(encoding="utf-8")


@pytest.fixture
def fake_umeos_repository(schedule_html: str) -> FakeUmeosRepository:
    return FakeUmeosRepository(schedule_html)


@pytest.fixture
def schedule_service(
    tmp_path: Path,
    fake_umeos_repository: FakeUmeosRepository,
) -> ScheduleService:
    return ScheduleService(
        chat_settings_repository=ChatSettingsRepository(tmp_path / "bot.db"),
        schedule_repository=ScheduleRepository(tmp_path / "schedules"),
        schedule_parser=ScheduleParser(),
        umeos_repository=fake_umeos_repository,
        today_factory=lambda: date(2026, 10, 5),
    )


async def test_set_group_saves_group_and_fetches_schedule(
    schedule_service: ScheduleService,
    fake_umeos_repository: FakeUmeosRepository,
) -> None:
    saved_group = await schedule_service.set_group(123, "  ОэУИТм-М05-26-1  ")

    today_schedule = await schedule_service.get_today_schedule(123)

    assert saved_group == "ОэУИТм-М05-26-1"
    assert today_schedule.group_name == "ОэУИТм-М05-26-1"
    assert today_schedule.day is not None
    assert len(today_schedule.day["courses"]) == 2
    assert fake_umeos_repository.calls == [("ОэУИТм-М05-26-1", FilterType.GROUP)]


async def test_get_today_schedule_requires_saved_group(schedule_service: ScheduleService) -> None:
    with pytest.raises(GroupNotSetError):
        await schedule_service.get_today_schedule(123)
