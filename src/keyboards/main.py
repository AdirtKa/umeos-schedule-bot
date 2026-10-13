from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

TODAY_BUTTON = "Расписание на сегодня"
GROUP_BUTTON = "Моя группа"
NOTIFY_BUTTON = "Напоминания"
SUPPORT_BUTTON = "Техподдержка"
CHANGES_BUTTON = "Изменения"
BROADCAST_BUTTON = "Написать всем"
HELP_BUTTON = "Помощь"


def get_main_keyboard(
    user_id: int | None = None,
    admin_user_id: int | None = None,
) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=TODAY_BUTTON)],
        [
            KeyboardButton(text=GROUP_BUTTON),
            KeyboardButton(text=NOTIFY_BUTTON),
        ],
        [
            KeyboardButton(text=SUPPORT_BUTTON),
            KeyboardButton(text=CHANGES_BUTTON),
        ],
        [KeyboardButton(text=HELP_BUTTON)],
    ]

    if admin_user_id is not None and user_id == admin_user_id:
        keyboard.insert(-1, [KeyboardButton(text=BROADCAST_BUTTON)])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выбери действие",
    )


main_keyboard = get_main_keyboard()
