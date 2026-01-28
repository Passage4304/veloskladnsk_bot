from aiogram.types import InlineKeyboardMarkup

from aiogram.utils.keyboard import InlineKeyboardButton

from data.data import CATEGORIES


def categories_kb(
    *,
    show_back: bool = False,
    back_callback: str = "back_button",
    row_width: int = 2.
) -> InlineKeyboardMarkup:
    keyboard = []
    row = []

    for key, name in CATEGORIES.items():
        row.append(
            InlineKeyboardButton(
                text=name,
                callback_data=f"cat:{key}"
            )
        )

        if len(row) == row_width:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)

    if show_back:
        keyboard.append([
            InlineKeyboardButton(
                text="Назад",
                callback_data=back_callback
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)