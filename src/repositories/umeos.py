from enum import StrEnum
from pathlib import Path

import requests


class FilterType(StrEnum):
    """Values for filter in url"""

    GROUP = "group"


class UmeosRepository:
    """Repository for getting data from a website."""

    def __init__(self) -> None:
        self.base_url: str = "https://umeos.ru/blocks/umerasp/json_rasper.php"

    def fetch_schedule(self, filter_value: str, filter_type: FilterType = FilterType.GROUP) -> str:
        response: requests.Response = requests.get(
            self.base_url, params={"type": filter_type.value, "groupname": filter_value}, timeout=10
        )

        response.raise_for_status()

        return response.text


def main() -> None:
    "Entrypoint."
    umeos_repository: UmeosRepository = UmeosRepository()
    path: Path = Path("./data/schedule.html")
    plain_text: str = umeos_repository.fetch_schedule("ОэУИТм-М05-26-1")
    with path.open("w", encoding="utf-8") as f:
        f.write(plain_text)


if __name__ == "__main__":
    main()
