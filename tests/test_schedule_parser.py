from pathlib import Path

import pytest

from src.parsers.schedule import ScheduleParser


@pytest.fixture
def parser() -> ScheduleParser:
    return ScheduleParser()


@pytest.fixture
def schedule_html() -> str:
    fixture_path = Path(__file__).parent / "fixtures" / "schedule.html"
    return fixture_path.read_text(encoding="utf-8")


@pytest.fixture
def parsed_schedule(
    parser: ScheduleParser,
    schedule_html: str,
) -> dict:
    return parser.parse_schedule(schedule_html)


def test_parse_schedule_returns_weeks(parsed_schedule: dict) -> None:
    assert "weeks" in parsed_schedule
    assert len(parsed_schedule["weeks"]) == 4


def test_parse_schedule_week_dates(parsed_schedule: dict) -> None:
    weeks = parsed_schedule["weeks"]

    assert "2026-10-05" in weeks
    assert "2026-10-12" in weeks
    assert "2026-10-19" in weeks
    assert "2026-10-26" in weeks


def test_parse_week_dates(parsed_schedule: dict) -> None:
    week = parsed_schedule["weeks"]["2026-10-05"]

    assert week["start_date"] == "2026-10-05"
    assert week["end_date"] == "2026-10-11"


def test_parse_week_days(parsed_schedule: dict) -> None:
    week = parsed_schedule["weeks"]["2026-10-05"]

    assert len(week["days"]) == 4

    assert week["days"][0]["date"] == "2026-10-05"
    assert week["days"][0]["day_of_week"] == "Понедельник"

    assert week["days"][1]["date"] == "2026-10-06"
    assert week["days"][1]["day_of_week"] == "Вторник"

    assert week["days"][2]["date"] == "2026-10-08"
    assert week["days"][2]["day_of_week"] == "Четверг"

    assert week["days"][3]["date"] == "2026-10-10"
    assert week["days"][3]["day_of_week"] == "Суббота"


def test_parse_day_courses(parsed_schedule: dict) -> None:
    monday = parsed_schedule["weeks"]["2026-10-05"]["days"][0]

    courses = monday["courses"]

    assert len(courses) == 2


def test_parse_course(parsed_schedule: dict) -> None:
    course = parsed_schedule["weeks"]["2026-10-05"]["days"][0]["courses"][0]

    assert course == {
        "number": "7",
        "start_time": "19:10",
        "end_time": "20:40",
        "room": "ЛВД-28",
        "description": (
            "Теория организации и организационное поведение Алексеева И.А. лекция вебинар"
        ),
    }


def test_parse_second_course(parsed_schedule: dict) -> None:
    course = parsed_schedule["weeks"]["2026-10-05"]["days"][0]["courses"][1]

    assert course["number"] == "8"
    assert course["start_time"] == "20:45"
    assert course["end_time"] == "22:15"
    assert course["room"] == "ЛВД-28"

    assert "практика" in course["description"]


def test_parse_schedule_empty_html(parser: ScheduleParser) -> None:
    result = parser.parse_schedule("")

    assert result == {"weeks": {}}
