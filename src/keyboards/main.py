from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

TODAY_BUTTON = "Расписание на сегодня"
GROUP_BUTTON = "Моя группа"
NOTIFY_BUTTON = "Напоминания"
HELP_BUTTON = "Помощь"

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=TODAY_BUTTON)],
        [
            KeyboardButton(text=GROUP_BUTTON),
            KeyboardButton(text=NOTIFY_BUTTON),
        ],
        [KeyboardButton(text=HELP_BUTTON)],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выбери действие",
)
