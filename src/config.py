from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: SecretStr
    log_level: str = "INFO"
    data_dir: Path = Path("data")
    db_path: Path | None = None
    schedules_dir: Path | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def set_data_paths(self) -> "Settings":
        if self.db_path is None:
            self.db_path = self.data_dir / "bot.db"

        if self.schedules_dir is None:
            self.schedules_dir = self.data_dir / "schedules"

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
