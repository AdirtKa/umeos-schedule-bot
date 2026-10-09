import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.config import get_settings
from src.dependencies import create_dependencies
from src.handlers import router
from src.jobs import BackgroundJobs
from src.logger import setup_logging
from src.middlewares import AccessLogMiddleware

logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level, settings.data_dir)
    dependencies = create_dependencies(settings)

    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(
        schedule_service=dependencies.schedule_service,
        notifier_service=dependencies.notifier_service,
    )
    dp.update.middleware(AccessLogMiddleware())
    dp.include_router(router)

    logger.info("Starting bot")
    jobs = BackgroundJobs(
        bot=bot,
        notifier_service=dependencies.notifier_service,
        schedule_updater=dependencies.schedule_updater,
    )
    jobs.start()

    try:
        await dp.start_polling(bot)
    finally:
        await jobs.stop()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
