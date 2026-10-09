from datetime import date
from html import escape
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from src.keyboards import GROUP_BUTTON, TODAY_BUTTON, main_keyboard
from src.services.schedule_service import (
    GroupNotSetError,
    ScheduleFetchError,
    ScheduleNotFoundError,
    ScheduleService,
    TodaySchedule,
)

router = Router()


@router.message(Command("group", "setgroup"))
async def set_group_handler(
    message: Message,
    command: CommandObject,
    schedule_service: ScheduleService,
) -> None:
    group_name = command.args.strip() if command.args else ""

    if not group_name:
        current_group = await schedule_service.get_group(message.chat.id)

        if current_group is None:
            await message.answer(
                "Группа для этого чата еще не задана.\nНапиши: /group НАЗВАНИЕ_ГРУППЫ",
                reply_markup=main_keyboard,
            )
            return

        await message.answer(
            f"Сейчас сохранена группа: <b>{escape(current_group)}</b>",
            reply_markup=main_keyboard,
        )
        return

    try:
        saved_group = await schedule_service.set_group(message.chat.id, group_name)
    except ScheduleNotFoundError:
        await message.answer(
            "Не нашел расписание для этой группы. Проверь название и попробуй еще раз.",
            reply_markup=main_keyboard,
        )
        return
    except ScheduleFetchError:
        await message.answer(
            "Не получилось получить расписание с umeos.ru. Попробуй повторить чуть позже.",
            reply_markup=main_keyboard,
        )
        return

    await message.answer(
        f"Группа сохранена: <b>{escape(saved_group)}</b>\n"
        "Теперь можно запросить расписание командой /today.",
        reply_markup=main_keyboard,
    )


@router.message(F.text == GROUP_BUTTON)
async def current_group_handler(
    message: Message,
    schedule_service: ScheduleService,
) -> None:
    current_group = await schedule_service.get_group(message.chat.id)

    if current_group is None:
        await message.answer(
            "Группа для этого чата еще не задана.\nНапиши: /group НАЗВАНИЕ_ГРУППЫ",
            reply_markup=main_keyboard,
        )
        return

    await message.answer(
        f"Сейчас сохранена группа: <b>{escape(current_group)}</b>\n"
        "Поменять можно так: /group НАЗВАНИЕ_ГРУППЫ",
        reply_markup=main_keyboard,
    )


@router.message(F.text == TODAY_BUTTON)
@router.message(Command("today", "schedule"))
async def today_schedule_handler(
    message: Message,
    schedule_service: ScheduleService,
) -> None:
    try:
        today_schedule = await schedule_service.get_today_schedule(message.chat.id)
    except GroupNotSetError:
        await message.answer(
            "Сначала нужно сохранить группу для этого чата.\nНапиши: /group НАЗВАНИЕ_ГРУППЫ",
            reply_markup=main_keyboard,
        )
        return
    except ScheduleNotFoundError:
        await message.answer(
            "Для сохраненной группы расписание не найдено. Проверь группу через /group.",
            reply_markup=main_keyboard,
        )
        return
    except ScheduleFetchError:
        await message.answer(
            "Не получилось обновить расписание с umeos.ru. Попробуй повторить чуть позже.",
            reply_markup=main_keyboard,
        )
        return

    await message.answer(format_today_schedule(today_schedule), reply_markup=main_keyboard)


def format_today_schedule(today_schedule: TodaySchedule) -> str:
    formatted_date = _format_date(today_schedule.target_date)
    group_name = escape(today_schedule.group_name)

    header = f"<b>Расписание на сегодня</b>\nГруппа: <b>{group_name}</b>\nДата: {formatted_date}"

    if today_schedule.day is None:
        return f"{header}\n\nЗанятий на сегодня нет."

    courses = today_schedule.day.get("courses", [])

    if not courses:
        return f"{header}\n\nЗанятий на сегодня нет."

    course_lines = [_format_course(course) for course in courses]
    return f"{header}\n\n" + "\n\n".join(course_lines)


def _format_course(course: dict[str, Any]) -> str:
    number = escape(str(course.get("number", "")))
    start_time = escape(str(course.get("start_time", "")))
    end_time = escape(str(course.get("end_time", "")))
    room = escape(str(course.get("room", "")))
    description = escape(str(course.get("description", "")))

    lines = [
        f"<b>{number} пара</b> {start_time}-{end_time}",
        description,
    ]

    if room:
        lines.append(f"Аудитория: {room}")

    return "\n".join(lines)


def _format_date(value: date) -> str:
    return value.strftime("%d.%m.%Y")
