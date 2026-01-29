from aiogram import types
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from keyboards.categories import categories_kb
from keyboards.common import back_kb
from keyboards.conditions import conditions_kb
from keyboards.photos import photos_kb


async def render_name(message: Message, state: FSMContext):
    data = await state.get_data()

    await message.bot.edit_message_text(
        chat_id=data["wizard_chat_id"],
        message_id=data["wizard_message_id"],
        text="Введите название для объявления:", 
        reply_markup=back_kb()
    )


async def render_category(message: Message, state: FSMContext):
    data = await state.get_data()

    await message.bot.edit_message_text(
        chat_id=data["wizard_chat_id"],
        message_id=data["wizard_message_id"],
        text="Выберите категорию для будущего объявления:", 
        reply_markup=categories_kb(show_back=True)
    )


async def render_condition(message: Message, state: FSMContext):
    data = await state.get_data()

    await message.bot.edit_message_text(
        chat_id=data["wizard_chat_id"],
        message_id=data["wizard_message_id"],
        text="Выберите состояние Вашего товара для объявления:", 
        reply_markup=conditions_kb(show_back=True)
    )


async def render_description(message: Message, state: FSMContext):
    data = await state.get_data()

    await message.bot.edit_message_text(
        chat_id=data["wizard_chat_id"],
        message_id=data["wizard_message_id"],
        text="Введите описание для объявления:", 
        reply_markup=back_kb()
    )


async def render_price(message: Message, state: FSMContext):
    data = await state.get_data()

    await message.bot.edit_message_text(
        chat_id=data["wizard_chat_id"],
        message_id=data["wizard_message_id"],
        text="Введите цену для объявления в рублях", 
        reply_markup=back_kb()
    )


async def render_photo(message: Message, state: FSMContext):
    data = await state.get_data()

    bot = message.bot

    try:
        await bot.delete_message(
            chat_id=data["wizard_chat_id"],
            message_id=data["wizard_message_id"]
        )
    except Exception:
        pass   


    new_wizard = await bot.send_message(
        chat_id=message.chat.id,
        text=(
            "Отправьте фотографии для объявления 📸\n"
            "Можно до 10 фото.\n\n"
            "Когда закончите — нажмите «Готово»."
        ),
        reply_markup=photos_kb()
    )


    await state.update_data(
        wizard_message_id=new_wizard.message_id,
        wizard_chat_id=new_wizard.chat.id
    )

