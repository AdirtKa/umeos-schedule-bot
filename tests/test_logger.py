import logging
from pathlib import Path

from src.logger import setup_logging


def test_setup_logging_writes_access_and_error_logs(tmp_path: Path) -> None:
    root_logger = logging.getLogger()
    setup_logging(data_dir=tmp_path)

    try:
        logger = logging.getLogger("test")
        logger.info("access message")
        logger.error("error message")

        for handler in root_logger.handlers:
            handler.flush()

        access_log = (tmp_path / "access.log").read_text(encoding="utf-8")
        error_log = (tmp_path / "error.log").read_text(encoding="utf-8")

        assert "access message" in access_log
        assert "error message" not in access_log
        assert "error message" in error_log
    finally:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            handler.close()
