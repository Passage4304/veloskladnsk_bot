from aiogram import types
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from keyboards.categories import categories_kb
from keyboards.common import back_kb
from keyboards.conditions import conditions_kb


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

    # Создаем новое сообщение с кнопкой "Готово" и "Отменить"
    sent = await message.answer(
        "Отправьте фотографии для объявления (до 10 шт).",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="✅ Готово", callback_data="photos_done"),
                    types.InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_ad"),
                ]
            ]
        )
    )

    # Сохраняем id этого сообщения в FSM, чтобы редактировать/удалять его при публикации или отмене
    await state.update_data(
        wizard_photo_message_id=sent.message_id,
        wizard_photo_chat_id=sent.chat.id,
        media_group=[],
        media_messages_ids=[]
    )

