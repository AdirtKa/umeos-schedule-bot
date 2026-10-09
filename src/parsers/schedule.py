from datetime import date as date_lib
from pathlib import Path
from pprint import pprint

from bs4 import BeautifulSoup, Tag


def parse_date_string(value: str) -> str:
    day, month, year = map(int, value.split("."))
    return date_lib(year, month, day).isoformat()


class ScheduleParser:
    def __init__(self):
        pass

    def parse_schedule(self, schedule: str) -> dict:
        soup = BeautifulSoup(schedule, "lxml")

        weeks: dict[str, dict] = {}

        for week in soup.select("div.tabs__content"):
            parsed_week = self.parse_week(week)
            weeks[parsed_week["start_date"]] = parsed_week

        return {"weeks": weeks}

    def parse_week(self, week: Tag) -> dict:
        start_date_raw, end_date_raw = self.parse_date(week)

        start_date = parse_date_string(start_date_raw)
        end_date = parse_date_string(end_date_raw)

        table_body = week.select_one("tbody")
        if table_body is None:
            raise ValueError("Week table body not found")

        days_set: list[dict] = []

        for day in table_body.select("th.cell.c0.lastcol"):
            day_of_week, date_raw = day.get_text(strip=True).split(" ", 1)

            date = parse_date_string(date_raw)

            days_set.append(
                {
                    "date": date,
                    "day_of_week": day_of_week,
                    "courses": self.parse_day(day),
                }
            )

        return {
            "start_date": start_date,
            "end_date": end_date,
            "days": days_set,
        }

    def parse_date(self, week: Tag) -> list[str]:
        date_tag: Tag = week.select("h3")[1]
        date: str = date_tag.text.lstrip("с ")
        return date.split(" по ", 2)

    def parse_day(self, day_header: Tag) -> list[dict[str, str]]:
        day_row: Tag = day_header.find_parent("tr")
        courses: list[dict[str, str]] = []

        if day_row is None:
            raise ValueError("Day row not found")

        row: Tag = day_row.find_next_sibling("tr")

        while row is not None:
            if row.find("th") is not None:
                break

            cells = row.select("td")

            if len(cells) >= 4:
                number = cells[0].get_text(strip=True)
                start_time, end_time = cells[1].get_text(strip=True).split("-", maxsplit=2)
                room = cells[2].get_text(strip=True)
                description = cells[3].get_text(" ", strip=True)

                day_info: dict[str, str] = {
                    "number": number,
                    "start_time": start_time,
                    "end_time": end_time,
                    "room": room,
                    "description": description,
                }
                courses.append(day_info)

            row = row.find_next_sibling("tr")

        return courses


def main() -> None:
    """Entry point."""
    test_file: Path = Path("data/schedule.html")
    schedule_parser = ScheduleParser()
    with test_file.open("r") as f:
        pprint(schedule_parser.parse_schedule(f.read()))  ## noqa T203


if __name__ == "__main__":
    main()
