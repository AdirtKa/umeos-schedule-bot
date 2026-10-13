from dataclasses import dataclass
from pathlib import Path

from src.config import Settings
from src.parsers.schedule import ScheduleParser
from src.repositories.chat_settings import ChatSettingsRepository
from src.repositories.schedule import ScheduleRepository
from src.repositories.support import SupportRepository
from src.services.notifier import NotifierService
from src.services.schedule_service import ScheduleService
from src.services.schedule_updater import ScheduleUpdater
from src.services.support import SupportService


@dataclass(frozen=True)
class AppDependencies:
    chat_settings_repository: ChatSettingsRepository
    schedule_service: ScheduleService
    notifier_service: NotifierService
    schedule_updater: ScheduleUpdater
    support_service: SupportService


def create_dependencies(settings: Settings) -> AppDependencies:
    db_path = settings.db_path or settings.data_dir / "bot.db"
    schedules_dir = settings.schedules_dir or settings.data_dir / "schedules"

    chat_settings_repository = ChatSettingsRepository(
        db_path=Path(db_path),
    )
    support_repository = SupportRepository(
        db_path=Path(db_path),
    )
    schedule_repository = ScheduleRepository(
        base_dir=Path(schedules_dir),
    )

    schedule_service = ScheduleService(
        chat_settings_repository=chat_settings_repository,
        schedule_repository=schedule_repository,
        schedule_parser=ScheduleParser(),
    )

    notifier_service = NotifierService(
        chat_settings_repository=chat_settings_repository,
        schedule_service=schedule_service,
    )

    schedule_updater = ScheduleUpdater(
        chat_settings_repository=chat_settings_repository,
        schedule_repository=schedule_repository,
        schedule_parser=ScheduleParser(),
    )
    support_service = SupportService(
        support_repository=support_repository,
    )

    return AppDependencies(
        chat_settings_repository=chat_settings_repository,
        schedule_service=schedule_service,
        notifier_service=notifier_service,
        schedule_updater=schedule_updater,
        support_service=support_service,
    )
