from datetime import UTC, datetime

from src.jobs import MOSCOW_TZ, seconds_until_next_daily_run


def test_seconds_until_next_daily_run_before_midnight_msk() -> None:
    now = datetime(2026, 10, 9, 23, 30, tzinfo=MOSCOW_TZ)

    assert seconds_until_next_daily_run(now) == 30 * 60


def test_seconds_until_next_daily_run_after_midnight_msk() -> None:
    now = datetime(2026, 10, 9, 0, 1, tzinfo=MOSCOW_TZ)

    assert seconds_until_next_daily_run(now) == (23 * 60 + 59) * 60


def test_seconds_until_next_daily_run_uses_moscow_timezone() -> None:
    now = datetime(2026, 10, 9, 20, 30, tzinfo=UTC)

    assert seconds_until_next_daily_run(now) == 30 * 60
