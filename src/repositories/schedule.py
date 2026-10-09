from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

_DISALLOWED_SLUG_CHARS = re.compile(r"[^a-z\u0430-\u044f\u04510-9_-]", re.IGNORECASE)


class ScheduleRepository:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _slugify(self, value: str) -> str:
        slug = value.strip().lower()

        slug = re.sub(r"\s+", "-", slug)
        slug = _DISALLOWED_SLUG_CHARS.sub("", slug)
        slug = re.sub(r"-+", "-", slug)

        return slug.strip("-_") or "group"

    def _get_path(self, group_name: str) -> Path:
        slug = self._slugify(group_name)

        group_hash = sha256(group_name.encode("utf-8")).hexdigest()[:8]

        filename = f"{slug}-{group_hash}.json"

        return self.base_dir / filename

    def write(
        self,
        group_name: str,
        schedule: dict[str, Any],
    ) -> None:
        path = self._get_path(group_name)
        temp_path = path.with_suffix(".tmp")

        data = {
            "group_name": group_name,
            **schedule,
        }

        temp_path.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        temp_path.replace(path)

    def read(
        self,
        group_name: str,
    ) -> dict[str, Any] | None:
        path = self._get_path(group_name)

        if not path.exists():
            return None

        return json.loads(path.read_text(encoding="utf-8"))

    def exists(self, group_name: str) -> bool:
        return self._get_path(group_name).exists()
