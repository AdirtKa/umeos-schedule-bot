from pathlib import Path

from src.config import Settings


def test_settings_defaults(monkeypatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test-token")

    settings = Settings(_env_file=None)

    assert settings.log_level == "INFO"
    assert settings.data_dir == Path("data")
    assert settings.db_path == Path("data") / "bot.db"
    assert settings.schedules_dir == Path("data") / "schedules"
