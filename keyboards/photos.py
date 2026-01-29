from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def photos_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Готово", callback_data="photos_done"),
                InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_ad"),
            ]
        ]
    )
