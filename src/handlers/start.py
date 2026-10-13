from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup

from src.keyboards import CHANGES_BUTTON, HELP_BUTTON, get_main_keyboard

router = Router()

HELP_TEXT = (
    "Я запоминаю группу для этого чата и показываю расписание на сегодня.\n\n"
    "Команды:\n"
    "/group НАЗВАНИЕ_ГРУППЫ - сохранить или поменять группу\n"
    "/group - показать сохраненную группу\n"
    "/today - расписание на сегодня\n"
    "/schedule - то же самое\n"
    "/notify 2 - напоминать за 2 часа до первой пары по МСК\n"
    "/notify 2h 30m - поставить несколько напоминаний\n"
    "/notify add 15m - добавить еще одно напоминание\n"
    "/notify remove 30m - удалить одно напоминание\n"
    "/notify off - выключить напоминания\n"
    "/support ТЕКСТ - написать в техподдержку\n"
    "/changes - что изменилось"
)

CHANGES_TEXT = (
    "<b>Что изменилось</b>\n\n"
    "- Добавлена техподдержка через тикеты: один пользователь - один тикет. "
    "Напиши /support и текст обращения.\n"
    "- Теперь можно поставить несколько напоминаний на один чат: /notify 2h 30m.\n"
    "- Напоминания можно задавать в минутах: /notify 45m.\n"
    "- Администратору доступна кнопка 'Написать всем' и команда /broadcast."
)


@router.message(CommandStart())
async def start_handler(message: Message, admin_user_id: int) -> None:
    await message.answer(HELP_TEXT, reply_markup=_reply_markup(message, admin_user_id))


@router.message(F.text == HELP_BUTTON)
@router.message(Command("help"))
async def help_handler(message: Message, admin_user_id: int) -> None:
    await message.answer(HELP_TEXT, reply_markup=_reply_markup(message, admin_user_id))


@router.message(F.text == CHANGES_BUTTON)
@router.message(Command("changes", "changelog"))
async def changes_handler(message: Message, admin_user_id: int) -> None:
    await message.answer(CHANGES_TEXT, reply_markup=_reply_markup(message, admin_user_id))


def _reply_markup(message: Message, admin_user_id: int) -> ReplyKeyboardMarkup:
    user_id = message.from_user.id if message.from_user else None
    return get_main_keyboard(user_id, admin_user_id)
