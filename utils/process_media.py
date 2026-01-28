from aiogram.types import InputMediaPhoto

from aiogram.fsm.context import FSMContext

from aiogram import Bot, types

from aiogram.types import (
    InputMediaPhoto,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from data.data import CATEGORIES, CONDITIONS

from states.user_add_ad import AddAdvertisement


async def process_media(
    message: types.Message,
    state: FSMContext,
    album: list[types.Message],
):
    data = await state.get_data()

    category_title = CATEGORIES[data["category"]]
    condition_title = CONDITIONS[data["condition"]]

    user_username = message.from_user.username

    seller_url = f'<a href="https://t.me/{user_username}">Написать продавцу</a>'

    caption = (
        f"#{category_title}\n"
        f"{data['name']}\n\n"
        f"Состояние:\n"
        f"#{condition_title}\n\n"
        f"Описание:\n{data['description']}\n\n"
        f"Цена: {data['price']}₽\n"
        f"{seller_url}\n\n"
    )

    media_group = []

    for i, msg in enumerate(album):
        file_id = msg.photo[-1].file_id

        if i == 0:
            media_group.append(
                InputMediaPhoto(
                    media=file_id,
                    caption=caption,
                    parse_mode="HTML",
                )
            )
        else:
            media_group.append(InputMediaPhoto(media=file_id))


    media_messages = await message.answer_media_group(media_group)

    await state.update_data(
        media_group=media_group,
        media_messages_ids=[msg.message_id for msg in media_messages]
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Опубликовать", callback_data="publish_ad"
                ),
                InlineKeyboardButton(
                    text="Отменить", callback_data="cancel_ad"
                ),
            ]
        ]
    )

    await message.answer(
        "Ваше объявление будет выглядеть так.\n"
        "Все верно? Публикуем в канале?",
        reply_markup=keyboard,
    )

    await state.set_state(AddAdvertisement.finish)


async def delete_media(
    bot: Bot,
    chat_id: int,
    message_ids: list[int],
):
    for msg_id in message_ids:
        try:
            await bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
