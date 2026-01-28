from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def single_button_kb(
    text: str,
    callback_data: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=text, 
            callback_data=callback_data
        )
    )
    return builder.as_markup()