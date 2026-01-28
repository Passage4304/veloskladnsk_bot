from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def back_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="back_button")]
        ]
    )