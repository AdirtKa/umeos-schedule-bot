import asyncio
from html import escape
import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, ReplyKeyboardMarkup

from src.keyboards import BROADCAST_BUTTON, SUPPORT_BUTTON, get_main_keyboard
from src.repositories.chat_settings import ChatSettingsRepository
from src.repositories.support import SupportTicket
from src.services.support import SupportService

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == SUPPORT_BUTTON)
async def support_button_handler(message: Message, admin_user_id: int) -> None:
    await message.answer(
        "Опиши проблему одним сообщением:\n/support текст обращения",
        reply_markup=_reply_markup(message, admin_user_id),
    )


@router.message(Command("support", "ticket"))
async def support_handler(
    message: Message,
    command: CommandObject,
    bot: Bot,
    support_service: SupportService,
    admin_user_id: int,
) -> None:
    if message.from_user is None:
        await message.answer(
            "Тикет можно создать только от имени пользователя.",
            reply_markup=_reply_markup(message, admin_user_id),
        )
        return

    text = command.args.strip() if command.args else ""

    if not text:
        await _answer_ticket_status(message, support_service, admin_user_id)
        return

    ticket = await support_service.open_ticket(message.from_user, text)
    await _notify_admin_about_ticket(bot, admin_user_id, ticket)
    await message.answer(
        f"Тикет #{ticket.user_id} отправлен в техподдержку. Ответ придет сюда.",
        reply_markup=_reply_markup(message, admin_user_id),
    )


@router.message(Command("tickets"))
async def tickets_handler(
    message: Message,
    support_service: SupportService,
    admin_user_id: int,
) -> None:
    if not _is_admin(message, admin_user_id):
        await _answer_admin_only(message, admin_user_id)
        return

    tickets = await support_service.get_open_tickets()

    if not tickets:
        await message.answer(
            "Открытых тикетов нет.",
            reply_markup=_reply_markup(message, admin_user_id),
        )
        return

    await message.answer(
        "<b>Открытые тикеты</b>\n\n"
        + "\n\n".join(_format_ticket_summary(ticket) for ticket in tickets),
        reply_markup=_reply_markup(message, admin_user_id),
    )


@router.message(Command("answer", "reply"))
async def answer_ticket_handler(
    message: Message,
    command: CommandObject,
    bot: Bot,
    support_service: SupportService,
    admin_user_id: int,
) -> None:
    if not _is_admin(message, admin_user_id):
        await _answer_admin_only(message, admin_user_id)
        return

    user_id, text = _parse_admin_targeted_text(command.args)

    if user_id is None or not text:
        await message.answer(
            "Формат ответа: /answer USER_ID текст ответа",
            reply_markup=_reply_markup(message, admin_user_id),
        )
        return

    ticket = await support_service.get_ticket(user_id)

    if ticket is None:
        await message.answer(
            "Не нашел тикет с таким USER_ID.",
            reply_markup=_reply_markup(message, admin_user_id),
        )
        return

    await bot.send_message(
        chat_id=user_id,
        text="<b>Ответ техподдержки</b>\n\n" + escape(text),
    )
    await message.answer(
        f"Ответ отправлен пользователю {user_id}.",
        reply_markup=_reply_markup(message, admin_user_id),
    )


@router.message(Command("close_ticket", "close"))
async def close_ticket_handler(
    message: Message,
    command: CommandObject,
    bot: Bot,
    support_service: SupportService,
    admin_user_id: int,
) -> None:
    if not _is_admin(message, admin_user_id):
        await _answer_admin_only(message, admin_user_id)
        return

    user_id = _parse_user_id(command.args)

    if user_id is None:
        await message.answer(
            "Формат закрытия: /close_ticket USER_ID",
            reply_markup=_reply_markup(message, admin_user_id),
        )
        return

    is_closed = await support_service.close_ticket(user_id)

    if not is_closed:
        await message.answer(
            "Не нашел тикет с таким USER_ID.",
            reply_markup=_reply_markup(message, admin_user_id),
        )
        return

    await bot.send_message(
        chat_id=user_id,
        text="Тикет закрыт. Если понадобится помощь, напиши /support и новый текст обращения.",
    )
    await message.answer(
        f"Тикет {user_id} закрыт.",
        reply_markup=_reply_markup(message, admin_user_id),
    )


@router.message(F.text == BROADCAST_BUTTON)
async def broadcast_button_handler(message: Message, admin_user_id: int) -> None:
    if not _is_admin(message, admin_user_id):
        await _answer_admin_only(message, admin_user_id)
        return

    await message.answer(
        "Напиши рассылку так:\n/broadcast текст сообщения",
        reply_markup=_reply_markup(message, admin_user_id),
    )


@router.message(Command("broadcast"))
async def broadcast_handler(
    message: Message,
    command: CommandObject,
    bot: Bot,
    chat_settings_repository: ChatSettingsRepository,
    admin_user_id: int,
) -> None:
    if not _is_admin(message, admin_user_id):
        await _answer_admin_only(message, admin_user_id)
        return

    text = command.args.strip() if command.args else ""

    if not text:
        await message.answer(
            "Формат рассылки: /broadcast текст сообщения",
            reply_markup=_reply_markup(message, admin_user_id),
        )
        return

    chat_ids = await asyncio.to_thread(chat_settings_repository.get_known_chat_ids)

    if not chat_ids:
        await message.answer(
            "Пока нет известных чатов для рассылки.",
            reply_markup=_reply_markup(message, admin_user_id),
        )
        return

    sent_count = 0
    failed_count = 0
    broadcast_text = "<b>Сообщение от администратора</b>\n\n" + escape(text)

    for chat_id in chat_ids:
        try:
            await bot.send_message(chat_id=chat_id, text=broadcast_text)
        except Exception:
            failed_count += 1
            logger.exception("Failed to broadcast message to chat %s", chat_id)
        else:
            sent_count += 1

    await message.answer(
        f"Рассылка завершена. Отправлено: {sent_count}, ошибок: {failed_count}.",
        reply_markup=_reply_markup(message, admin_user_id),
    )


async def _answer_ticket_status(
    message: Message,
    support_service: SupportService,
    admin_user_id: int,
) -> None:
    if message.from_user is None:
        return

    ticket = await support_service.get_ticket(message.from_user.id)

    if ticket is None:
        await message.answer(
            "Тикета пока нет. Опиши проблему так:\n/support текст обращения",
            reply_markup=_reply_markup(message, admin_user_id),
        )
        return

    await message.answer(
        f"Твой тикет #{ticket.user_id}: {escape(ticket.status)}.\n"
        "Добавить новое сообщение можно так:\n/support текст обращения",
        reply_markup=_reply_markup(message, admin_user_id),
    )


async def _notify_admin_about_ticket(
    bot: Bot,
    admin_user_id: int,
    ticket: SupportTicket,
) -> None:
    username = f"@{ticket.username}" if ticket.username else "без username"
    text = (
        "<b>Тикет техподдержки</b>\n"
        f"ID: <code>{ticket.user_id}</code>\n"
        f"Пользователь: {escape(ticket.full_name)} ({escape(username)})\n"
        f"Статус: {escape(ticket.status)}\n\n"
        f"{escape(ticket.last_message)}\n\n"
        f"Ответить: <code>/answer {ticket.user_id} текст</code>\n"
        f"Закрыть: <code>/close_ticket {ticket.user_id}</code>"
    )

    await bot.send_message(chat_id=admin_user_id, text=text)


def _format_ticket_summary(ticket: SupportTicket) -> str:
    username = f"@{ticket.username}" if ticket.username else "без username"
    return (
        f"<code>{ticket.user_id}</code> - {escape(ticket.full_name)} ({escape(username)})\n"
        f"{escape(ticket.last_message)}"
    )


def _parse_admin_targeted_text(args: str | None) -> tuple[int | None, str]:
    if not args:
        return None, ""

    parts = args.strip().split(maxsplit=1)

    if len(parts) < 2:
        return None, ""

    user_id = _parse_user_id(parts[0])

    if user_id is None:
        return None, ""

    return user_id, parts[1].strip()


def _parse_user_id(value: str | None) -> int | None:
    if not value:
        return None

    try:
        return int(value.strip())
    except ValueError:
        return None


async def _answer_admin_only(message: Message, admin_user_id: int) -> None:
    await message.answer(
        "Эта команда доступна только администратору.",
        reply_markup=_reply_markup(message, admin_user_id),
    )


def _is_admin(message: Message, admin_user_id: int) -> bool:
    return message.from_user is not None and message.from_user.id == admin_user_id


def _reply_markup(message: Message, admin_user_id: int) -> ReplyKeyboardMarkup:
    user_id = message.from_user.id if message.from_user else None
    return get_main_keyboard(user_id, admin_user_id)
