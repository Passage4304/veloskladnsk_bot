from aiogram.types import InlineKeyboardMarkup

from aiogram.utils.keyboard import InlineKeyboardButton

from data.data import CONDITIONS


def conditions_kb(
    *,
    show_back: bool = False,
    back_callback: str = "back_button",
    row_width: int = 2,
) -> InlineKeyboardMarkup:
    keyboard = []
    row = []

    for key, name in CONDITIONS.items():
        row.append(
            InlineKeyboardButton(
                text=name,
                callback_data=f"cond:{key}"
            )
        )

        if len(row) == 2:
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