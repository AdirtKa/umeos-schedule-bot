from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from src.keyboards import HELP_BUTTON, main_keyboard

router = Router()

HELP_TEXT = (
    "Я запоминаю группу для этого чата и показываю расписание на сегодня.\n\n"
    "Команды:\n"
    "/group НАЗВАНИЕ_ГРУППЫ - сохранить или поменять группу\n"
    "/group - показать сохраненную группу\n"
    "/today - расписание на сегодня\n"
    "/schedule - то же самое\n"
    "/notify 2 - напоминать за 2 часа до первой пары по МСК\n"
    "/notify off - выключить напоминания"
)


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_keyboard)


@router.message(F.text == HELP_BUTTON)
@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_keyboard)
