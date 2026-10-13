from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup

from src.keyboards import CHANGES_BUTTON, HELP_BUTTON, get_main_keyboard

router = Router()

USER_HELP_TEXT = (
    "<b>Помощь по боту</b>\n\n"
    "Я запоминаю группу для этого чата, показываю расписание на сегодня и отправляю "
    "напоминания перед первой парой по МСК.\n\n"
    "<b>Основные команды</b>\n"
    "/start - открыть стартовое сообщение\n"
    "/help - показать эту помощь\n"
    "/changes - список последних изменений\n\n"
    "<b>Расписание</b>\n"
    "/group НАЗВАНИЕ_ГРУППЫ - сохранить или поменять группу\n"
    "/group - показать сохраненную группу\n"
    "/today - расписание на сегодня\n"
    "/schedule - то же самое, что /today\n\n"
    "<b>Напоминания</b>\n"
    "/notify - показать текущие напоминания\n"
    "/notify 2 - напоминать за 2 часа\n"
    "/notify 45m - напоминать за 45 минут\n"
    "/notify 2h 30m - поставить несколько напоминаний\n"
    "/notify add 15m - добавить еще одно напоминание\n"
    "/notify remove 30m - удалить одно напоминание\n"
    "/notify off - выключить все напоминания\n\n"
    "<b>Техподдержка</b>\n"
    "/support ТЕКСТ - отправить обращение в техподдержку\n"
    "/support - посмотреть статус своего тикета"
)

ADMIN_HELP_TEXT = (
    "\n\n<b>Админ-команды</b>\n"
    "/tickets - список открытых тикетов с inline-кнопками\n"
    "/answer USER_ID ТЕКСТ - ответить пользователю по тикету\n"
    "/close_ticket USER_ID - закрыть тикет\n"
    "/broadcast ТЕКСТ - написать всем известным чатам\n\n"
    "В уведомлениях о тикетах есть кнопки: Ответить, Закрыть, Профиль и Все тикеты."
)

CHANGES_TEXT = (
    "<b>Что изменилось</b>\n\n"
    "- Добавлена техподдержка через тикеты: один пользователь - один тикет. "
    "Напиши /support и текст обращения.\n"
    "- Теперь можно поставить несколько напоминаний на один чат: /notify 2h 30m.\n"
    "- Напоминания можно задавать в минутах: /notify 45m.\n"
    "- Администратору доступна кнопка 'Написать всем' и команда /broadcast.\n"
    "- В тикетах появились inline-кнопки для админа: Ответить, Закрыть, Профиль и Все тикеты."
)


@router.message(CommandStart())
async def start_handler(message: Message, admin_user_id: int) -> None:
    await message.answer(
        _help_text(message, admin_user_id),
        reply_markup=_reply_markup(message, admin_user_id),
    )


@router.message(F.text == HELP_BUTTON)
@router.message(Command("help"))
async def help_handler(message: Message, admin_user_id: int) -> None:
    await message.answer(
        _help_text(message, admin_user_id),
        reply_markup=_reply_markup(message, admin_user_id),
    )


@router.message(F.text == CHANGES_BUTTON)
@router.message(Command("changes", "changelog"))
async def changes_handler(message: Message, admin_user_id: int) -> None:
    await message.answer(CHANGES_TEXT, reply_markup=_reply_markup(message, admin_user_id))


def _reply_markup(message: Message, admin_user_id: int) -> ReplyKeyboardMarkup:
    user_id = message.from_user.id if message.from_user else None
    return get_main_keyboard(user_id, admin_user_id)


def _help_text(message: Message, admin_user_id: int) -> str:
    user_id = message.from_user.id if message.from_user else None

    if user_id == admin_user_id:
        return USER_HELP_TEXT + ADMIN_HELP_TEXT

    return USER_HELP_TEXT
