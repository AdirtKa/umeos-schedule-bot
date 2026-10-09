import logging
from pathlib import Path
from typing import Final

ACCESS_LOGGER_NAME: Final = "access"
ERROR_LOGGER_NAME: Final = "error"
ACCESS_LOG_FILE: Final = "access.log"
ERROR_LOG_FILE: Final = "error.log"


class MaxLevelFilter(logging.Filter):
    def __init__(self, max_level: int) -> None:
        super().__init__()
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno < self.max_level


def setup_logging(level: str = "INFO", data_dir: Path | str = "data") -> None:
    log_dir = Path(data_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    log_level = _resolve_level(level)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    _clear_handlers(root_logger)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    access_handler = logging.FileHandler(log_dir / ACCESS_LOG_FILE, encoding="utf-8")
    access_handler.setLevel(log_level)
    access_handler.addFilter(MaxLevelFilter(logging.ERROR))
    access_handler.setFormatter(formatter)

    error_handler = logging.FileHandler(log_dir / ERROR_LOG_FILE, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(access_handler)
    root_logger.addHandler(error_handler)


def get_access_logger() -> logging.Logger:
    return logging.getLogger(ACCESS_LOGGER_NAME)


def get_error_logger() -> logging.Logger:
    return logging.getLogger(ERROR_LOGGER_NAME)


def _resolve_level(level: str) -> int:
    resolved_level = logging.getLevelName(level.upper())
    if isinstance(resolved_level, int):
        return resolved_level

    return logging.INFO


def _clear_handlers(logger: logging.Logger) -> None:
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
