from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from src.keyboards import NOTIFY_BUTTON, main_keyboard
from src.services.notifier import NotifierService
from src.services.schedule_service import ScheduleService

router = Router()

MIN_REMINDER_HOURS = 0
MAX_REMINDER_HOURS = 24


@router.message(Command("notify", "remind"))
async def notify_handler(
    message: Message,
    command: CommandObject,
    schedule_service: ScheduleService,
    notifier_service: NotifierService,
) -> None:
    args = command.args.strip() if command.args else ""

    if not args:
        await _answer_current_settings(message, schedule_service, notifier_service)
        return

    if args.lower() in {"off", "disable", "выкл", "отключить"}:
        await _disable_reminders(message, notifier_service)
        return

    try:
        hours_before = int(args)
    except ValueError:
        await message.answer("Укажи целое число часов: /notify 2", reply_markup=main_keyboard)
        return

    if not MIN_REMINDER_HOURS <= hours_before <= MAX_REMINDER_HOURS:
        await message.answer(
            "Можно выбрать от 0 до 24 часов: /notify 2", reply_markup=main_keyboard
        )
        return

    group_name = await schedule_service.get_group(message.chat.id)

    if group_name is None:
        await message.answer(
            "Сначала нужно сохранить группу для этого чата.\nНапиши: /group НАЗВАНИЕ_ГРУППЫ",
            reply_markup=main_keyboard,
        )
        return

    is_saved = await notifier_service.set_reminder_hours(message.chat.id, hours_before)

    if not is_saved:
        await message.answer(
            "Сначала нужно сохранить группу для этого чата.\nНапиши: /group НАЗВАНИЕ_ГРУППЫ",
            reply_markup=main_keyboard,
        )
        return

    await message.answer(
        f"Напоминания включены: один раз в день за {hours_before} ч. до первой пары по МСК.",
        reply_markup=main_keyboard,
    )


async def _answer_current_settings(
    message: Message,
    schedule_service: ScheduleService,
    notifier_service: NotifierService,
) -> None:
    group_name = await schedule_service.get_group(message.chat.id)

    if group_name is None:
        await message.answer(
            "Группа для этого чата еще не задана.\nСначала напиши: /group НАЗВАНИЕ_ГРУППЫ",
            reply_markup=main_keyboard,
        )
        return

    hours_before = await notifier_service.get_reminder_hours(message.chat.id)

    if hours_before is None:
        await message.answer(
            "Напоминания выключены. Включить можно так: /notify 2",
            reply_markup=main_keyboard,
        )
        return

    await message.answer(
        f"Напоминания включены: один раз в день за {hours_before} ч. до первой пары по МСК.",
        reply_markup=main_keyboard,
    )


async def _disable_reminders(
    message: Message,
    notifier_service: NotifierService,
) -> None:
    is_disabled = await notifier_service.disable_reminders(message.chat.id)

    if not is_disabled:
        await message.answer(
            "Для этого чата пока нет сохраненных настроек.",
            reply_markup=main_keyboard,
        )
        return

    await message.answer("Напоминания выключены.", reply_markup=main_keyboard)


@router.message(F.text == NOTIFY_BUTTON)
async def notify_button_handler(
    message: Message,
    schedule_service: ScheduleService,
    notifier_service: NotifierService,
) -> None:
    await _answer_current_settings(message, schedule_service, notifier_service)
