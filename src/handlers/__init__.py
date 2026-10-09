from aiogram import Router

from src.handlers.notifier import router as notifier_router
from src.handlers.schedule import router as schedule_router
from src.handlers.start import router as start_router

router = Router()
router.include_router(start_router)
router.include_router(schedule_router)
router.include_router(notifier_router)
