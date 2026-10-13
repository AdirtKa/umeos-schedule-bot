import re

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, ReplyKeyboardMarkup

from src.keyboards import NOTIFY_BUTTON, get_main_keyboard
from src.services.notifier import NotifierService, format_reminder_delta
from src.services.schedule_service import ScheduleService

router = Router()

MIN_REMINDER_MINUTES = 0
MAX_REMINDER_MINUTES = 24 * 60

ADD_ACTIONS = {"add", "добавить", "плюс", "+"}
REMOVE_ACTIONS = {"remove", "delete", "del", "rm", "удалить", "минус", "-"}
OFF_ACTIONS = {"off", "disable", "выкл", "отключить"}


@router.message(Command("notify", "remind"))
async def notify_handler(
    message: Message,
    command: CommandObject,
    schedule_service: ScheduleService,
    notifier_service: NotifierService,
    admin_user_id: int,
) -> None:
    args = command.args.strip() if command.args else ""

    if not args:
        await _answer_current_settings(message, schedule_service, notifier_service, admin_user_id)
        return

    if args.lower() in OFF_ACTIONS:
        await _disable_reminders(message, notifier_service, admin_user_id)
        return

    action, duration_text = _parse_action(args)

    try:
        reminder_minutes = _parse_reminder_minutes(duration_text)
    except ValueError:
        await message.answer(
            "Укажи время от 0 до 24 часов: /notify 2h 30m или /notify 45m",
            reply_markup=_reply_markup(message, admin_user_id),
        )
        return

    group_name = await schedule_service.get_group(message.chat.id)

    if group_name is None:
        await message.answer(
            "Сначала нужно сохранить группу для этого чата.\nНапиши: /group НАЗВАНИЕ_ГРУППЫ",
            reply_markup=_reply_markup(message, admin_user_id),
        )
        return

    is_saved = await _save_reminders(message.chat.id, action, reminder_minutes, notifier_service)

    if not is_saved:
        await message.answer(
            "Сначала нужно сохранить группу для этого чата.\nНапиши: /group НАЗВАНИЕ_ГРУППЫ",
            reply_markup=_reply_markup(message, admin_user_id),
        )
        return

    current_reminders = await notifier_service.get_reminder_minutes(message.chat.id)
    await message.answer(
        _format_save_result(action, current_reminders),
        reply_markup=_reply_markup(message, admin_user_id),
    )


async def _answer_current_settings(
    message: Message,
    schedule_service: ScheduleService,
    notifier_service: NotifierService,
    admin_user_id: int,
) -> None:
    group_name = await schedule_service.get_group(message.chat.id)

    if group_name is None:
        await message.answer(
            "Группа для этого чата еще не задана.\nСначала напиши: /group НАЗВАНИЕ_ГРУППЫ",
            reply_markup=_reply_markup(message, admin_user_id),
        )
        return

    reminder_minutes = await notifier_service.get_reminder_minutes(message.chat.id)

    if not reminder_minutes:
        await message.answer(
            "Напоминания выключены. Включить можно так: /notify 2h 30m",
            reply_markup=_reply_markup(message, admin_user_id),
        )
        return

    await message.answer(
        "Напоминания включены: "
        f"{_format_reminder_list(reminder_minutes)} до первой пары по МСК.\n"
        "Добавить: /notify add 15m\n"
        "Удалить одно: /notify remove 30m",
        reply_markup=_reply_markup(message, admin_user_id),
    )


async def _disable_reminders(
    message: Message,
    notifier_service: NotifierService,
    admin_user_id: int,
) -> None:
    is_disabled = await notifier_service.disable_reminders(message.chat.id)

    if not is_disabled:
        await message.answer(
            "Для этого чата пока нет сохраненных настроек.",
            reply_markup=_reply_markup(message, admin_user_id),
        )
        return

    await message.answer(
        "Напоминания выключены.",
        reply_markup=_reply_markup(message, admin_user_id),
    )


@router.message(F.text == NOTIFY_BUTTON)
async def notify_button_handler(
    message: Message,
    schedule_service: ScheduleService,
    notifier_service: NotifierService,
    admin_user_id: int,
) -> None:
    await _answer_current_settings(message, schedule_service, notifier_service, admin_user_id)


async def _save_reminders(
    chat_id: int,
    action: str,
    reminder_minutes: list[int],
    notifier_service: NotifierService,
) -> bool:
    if action == "add":
        return await notifier_service.add_reminder_minutes(chat_id, reminder_minutes)

    if action == "remove":
        return await notifier_service.remove_reminder_minutes(chat_id, reminder_minutes)

    return await notifier_service.set_reminder_minutes(chat_id, reminder_minutes)


def _parse_action(args: str) -> tuple[str, str]:
    tokens = args.split(maxsplit=1)
    first_token = tokens[0].lower()

    if first_token in ADD_ACTIONS:
        return "add", tokens[1] if len(tokens) > 1 else ""

    if first_token in REMOVE_ACTIONS:
        return "remove", tokens[1] if len(tokens) > 1 else ""

    return "set", args


def _parse_reminder_minutes(value: str) -> list[int]:
    tokens = [token for token in re.split(r"[\s,;]+", value.strip()) if token]

    if not tokens:
        raise ValueError

    reminders = [_parse_duration_token(token) for token in tokens]
    return sorted(set(reminders), reverse=True)


def _parse_duration_token(token: str) -> int:
    match = re.fullmatch(r"(?P<value>\d+)(?P<unit>[a-zа-я]*)", token.lower())

    if match is None:
        raise ValueError

    value = int(match.group("value"))
    unit = match.group("unit")

    if unit in {"", "h", "hr", "hrs", "hour", "hours", "ч", "час", "часа", "часов"}:
        minutes = value * 60
    elif unit in {"m", "min", "mins", "minute", "minutes", "м", "мин", "минута", "минуты", "минут"}:
        minutes = value
    else:
        raise ValueError

    if not MIN_REMINDER_MINUTES <= minutes <= MAX_REMINDER_MINUTES:
        raise ValueError

    return minutes


def _format_save_result(action: str, reminder_minutes: list[int]) -> str:
    if not reminder_minutes:
        return "Готово. Напоминаний для этого чата больше нет."

    reminders = _format_reminder_list(reminder_minutes)

    if action == "add":
        return f"Добавил напоминание. Сейчас включено: {reminders} до первой пары по МСК."

    if action == "remove":
        return f"Обновил напоминания. Сейчас включено: {reminders} до первой пары по МСК."

    return f"Напоминания обновлены: {reminders} до первой пары по МСК."


def _format_reminder_list(reminder_minutes: list[int]) -> str:
    return ", ".join(f"за {format_reminder_delta(minutes)}" for minutes in reminder_minutes)


def _reply_markup(message: Message, admin_user_id: int) -> ReplyKeyboardMarkup:
    user_id = message.from_user.id if message.from_user else None
    return get_main_keyboard(user_id, admin_user_id)
