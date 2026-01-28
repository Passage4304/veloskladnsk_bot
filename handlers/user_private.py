import os

from aiogram import Bot, types, Router, F

from aiogram.types import Message

from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext

from keyboards.common import back_kb
from states.user_add_ad import AddAdvertisement

from ui.render import render_category, render_condition, render_description, render_name, render_price
from utils.process_media import process_media, delete_media
from utils.wizard import pop_state, push_state

from keyboards.categories import categories_kb
from keyboards.conditions import conditions_kb
from keyboards.start import single_button_kb


from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


ADS_CHAT_ID = os.getenv("ADS_CHAT_ID")
ADS_CHAT_NAME = os.getenv("ADS_CHAT_NAME")


user_private_router = Router()


async def render_by_state(message: Message, state: FSMContext, fsm_state):
    if fsm_state == AddAdvertisement.name:
        await render_name(message, state)
    elif fsm_state == AddAdvertisement.category:
        await render_category(message, state)
    elif fsm_state == AddAdvertisement.condition:
        await render_condition(message, state)
    elif fsm_state == AddAdvertisement.description:
        await render_description(message, state)


@user_private_router.message(CommandStart())
async def start_command(message: types.Message):
    await message.answer(
        'Привет! Я помогу разместить объявление о продаже.\nДля создания объявления нажми кнопку "Создать объявление" ниже',
        reply_markup=single_button_kb(
            text="Создать объявление",
            callback_data="create_ad"
        ),
    )


@user_private_router.callback_query(StateFilter(None), F.data == "create_ad")
async def create_ad_start(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(
        wizard_message_id=callback.message.message_id,
        wizard_chat_id = callback.message.chat.id
    )

    await callback.answer()

    await state.set_state(AddAdvertisement.name)

    await push_state(state, AddAdvertisement.name)

    await render_name(callback.message, state)


@user_private_router.callback_query(F.data == "back_button")
async def back_handler(callback: types.CallbackQuery, state: FSMContext):
    prev_state = await pop_state(state)

    if not prev_state:
        await callback.answer("Вы на первом шаге")
        return

    await state.set_state(prev_state)
    await render_by_state(callback.message, state, prev_state)
    

@user_private_router.message(StateFilter(AddAdvertisement.name), F.text)
async def create_ad_choose_category(message: types.Message, state: FSMContext, bot: Bot):
    await state.update_data(name=message.text)

    next_state = AddAdvertisement.category

    await push_state(state, next_state)
    await state.set_state(next_state)
    await render_category(message, state)


@user_private_router.callback_query(StateFilter(AddAdvertisement.category), F.data.startswith("cat:"))
async def create_ad_choose_condition(callback: types.CallbackQuery, state: FSMContext):
    category_key = callback.data.split(":")[1]
    await state.update_data(category=category_key)
    
    next_state = AddAdvertisement.condition

    await push_state(state, next_state)
    await state.set_state(next_state)
    await render_condition(callback.message, state)


@user_private_router.callback_query(StateFilter(AddAdvertisement.condition), F.data.startswith("cond:"))
async def create_ad_condition_selected(callback: types.CallbackQuery, state: FSMContext):
    condition_key = callback.data.split(":")[1]
    await state.update_data(condition=condition_key)

    next_state = AddAdvertisement.description

    await push_state(state, next_state)
    await state.set_state(next_state)
    await render_condition(callback.message, state)


@user_private_router.message(StateFilter(AddAdvertisement.description), F.text)
async def create_ad_add_description(message: types.Message, state: FSMContext, bot: Bot):
    await state.update_data(description=message.text)

    next_state = AddAdvertisement.price

    await push_state(state, next_state)
    await state.set_state(next_state)
    await render_condition(message, state)


@user_private_router.message(StateFilter(AddAdvertisement.price), F.text)
async def create_ad_add_price(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    wizard_message_id = data["wizard_message_id"]
    wizard_chat_id = data["wizard_chat_id"]


    if not message.text.isdigit():
        await bot.edit_message_text(
            message_id=wizard_message_id, 
            chat_id=wizard_chat_id,
            text="Ошибка\nВведите, пожалуйста, корректное число для цены"
        )
        return
    await state.update_data(price=message.text)
    await bot.edit_message_text(
        message_id=wizard_message_id, 
        chat_id=wizard_chat_id,
        text="Отправьте фотографии для объявления"
    )

    next_state = AddAdvertisement.photo

    await push_state(state, next_state)
    await state.set_state(next_state)
    await render_condition(message, state)


@user_private_router.message(
    StateFilter(AddAdvertisement.photo), F.media_group_id
)
async def create_ad_add_media_group(
    message: types.Message,
    state: FSMContext,
    album: list[Message],
):
    await process_media(
        message=message,
        state=state,
        album=album,
    )


@user_private_router.message(
        StateFilter(AddAdvertisement.photo),
        F.photo
)
async def create_add_add_single_photo(
    message: types.Message,
    state: FSMContext,
):
    await process_media(
        message=message,
        state=state,
        album=[message],
    )


@user_private_router.callback_query(
    StateFilter(AddAdvertisement.finish), F.data == "publish_ad"
)
async def create_ad_publish(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()

    sended_message = await bot.send_media_group(
        chat_id=ADS_CHAT_ID, media=data["media_group"]
    )

    chat_url = f"https://t.me/{ADS_CHAT_NAME}/{sended_message[0].message_id}"

    await callback.answer("Спасибо!\nОбъявление успешно опубликовано!")
    await callback.message.edit_text(
        "Спасибо!\n"
        f"Ваше объявление успешно опубликовано!\n"
        f"Оно доступно по ссылке:\n{chat_url}\n",
        reply_markup=single_button_kb(
            text="Создать еще одно!",
            callback_data="create_ad"
        )
    )

    await delete_media(
        bot=bot,
        chat_id=callback.message.chat.id,
        message_ids=data.get("media_messages_ids", [])
    )

    await state.clear()


@user_private_router.callback_query(
    StateFilter(AddAdvertisement.finish), F.data == "cancel_ad"
)
async def create_ad_cancel(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()

    await delete_media(
        bot=bot,
        chat_id=callback.message.chat.id,
        message_ids=data.get("media_messages_ids", [])
    )

    await callback.answer("Публикация отменена")
    await callback.message.edit_text(
        "Публикация объявления отменена...\n", 
            reply_markup=single_button_kb(
            text="Создать объявление повторно",
            callback_data="create_ad"
        )
    )

    await state.clear()
