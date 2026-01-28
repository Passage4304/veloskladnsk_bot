import os

from aiogram import Bot, types, Router, F

from aiogram.types import Message

from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext

from states.user_add_ad import AddAdvertisement

from utils.process_media import process_media, delete_media

from keyboards.categories import categories_kb
from keyboards.conditions import conditions_kb
from keyboards.start import single_button_kb


from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


ADS_CHAT_ID = os.getenv("ADS_CHAT_ID")
ADS_CHAT_NAME = os.getenv("ADS_CHAT_NAME")


user_private_router = Router()


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
    await callback.answer()
    await callback.message.edit_text("Введите название для объявления:")
    await state.set_state(AddAdvertisement.name)


@user_private_router.callback_query(StateFilter("*"), F.data == "back_button")
async def back_step_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    current_state = await state.get_state()

    if current_state == AddAdvertisement.name:
        await callback.answer(
            "Вы находитесь на первом шаге.\n"
            "Возвращаться некуда..."
        )
        return
    
    previous = None

    for step in AddAdvertisement.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await callback.message.edit_text(
                f"Вы вернулись к предыдущему шагу\n{AddAdvertisement.texts[previous.state]}"
            )
        previous = step


@user_private_router.message(StateFilter(AddAdvertisement.name), F.text)
async def create_ad_choose_category(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(
        "Выберите категорию для будущего объявления:", 
        reply_markup=categories_kb(show_back=True)
    )
    await state.set_state(AddAdvertisement.category)


@user_private_router.callback_query(StateFilter(AddAdvertisement.category), F.data.startswith("cat:"))
async def create_ad_choose_condition(callback: types.CallbackQuery, state: FSMContext):
    category_key = callback.data.split(":")[1]
    
    await state.update_data(category=category_key)
    await state.set_state(AddAdvertisement.condition)

    await callback.message.edit_text(
        "Выберите состояние Вашего товара для объявления:", 
        reply_markup=conditions_kb(show_back=True)
    )


@user_private_router.callback_query(StateFilter(AddAdvertisement.condition), F.data.startswith("cond:"))
async def create_ad_condition_selected(callback: types.CallbackQuery, state: FSMContext):
    condition_key = callback.data.split(":")[1]

    await state.update_data(condition=condition_key)
    await state.set_state(AddAdvertisement.description)

    await callback.message.edit_text(
        "Введите описание для объявления:"
    )


@user_private_router.message(StateFilter(AddAdvertisement.description), F.text)
async def create_ad_add_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите цену для объявления в рублях")
    await state.set_state(AddAdvertisement.price)


@user_private_router.message(StateFilter(AddAdvertisement.price), F.text)
async def create_ad_add_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Ошибка\nВведите, пожалуйста, корректное число для цены")
        return
    await state.update_data(price=message.text)
    await message.answer("Отправьте фотографии для объявления")
    await state.set_state(AddAdvertisement.photo)


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
