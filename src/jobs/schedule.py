from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

MOSCOW_TZ = ZoneInfo("Europe/Moscow")


def seconds_until_next_daily_run(
    now: datetime,
    run_at: time = time(hour=0),
) -> float:
    moscow_now = _as_moscow_time(now)
    next_run = datetime.combine(moscow_now.date(), run_at, tzinfo=MOSCOW_TZ)

    if next_run <= moscow_now:
        next_run += timedelta(days=1)

    return (next_run - moscow_now).total_seconds()


def _as_moscow_time(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=MOSCOW_TZ)

    return value.astimezone(MOSCOW_TZ)
