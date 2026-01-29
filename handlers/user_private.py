import os

from aiogram import Bot, types, Router, F

from aiogram.types import Message

from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext

from data.data import CATEGORIES, CONDITIONS
from keyboards.common import back_kb
from states.user_add_ad import AddAdvertisement

from ui.render import render_category, render_condition, render_description, render_name, render_photo, render_price
from utils.process_media import process_media, delete_media
from utils.wizard import pop_state, push_state

from keyboards.categories import categories_kb
from keyboards.conditions import conditions_kb
from keyboards.start import single_button_kb


from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


ADS_CHAT_ID = os.getenv("ADS_CHAT_ID")
ADS_CHAT_NAME = os.getenv("ADS_CHAT_NAME")
MAX_PHOTOS = 10


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
    elif fsm_state == AddAdvertisement.price:
        await render_price(message, state)
    elif fsm_state == AddAdvertisement.photo:
        await render_photo(message, state)
    elif fsm_state == AddAdvertisement.preview:
        # Если возвращаемся на шаг preview, нужно отправить сообщение
        data = await state.get_data()
        await message.answer(
            "Вы на шаге предпросмотра объявления. Используйте кнопки для действий.",
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(text="✅ Опубликовать", callback_data="publish_ad"),
                        types.InlineKeyboardButton(text="↩️ Назад к фото", callback_data="back_to_photos"),
                    ]
                ]
            )
        )

async def delete_old_wizard_message(state: FSMContext, bot: Bot):
    """Удаляет старое wizard-сообщение при переходе на новый шаг"""
    try:
        data = await state.get_data()
        wizard_message_id = data.get("wizard_message_id")
        wizard_chat_id = data.get("wizard_chat_id")
        if wizard_message_id and wizard_chat_id:
            await bot.delete_message(
                chat_id=wizard_chat_id,
                message_id=wizard_message_id
            )
    except Exception:
        pass


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
    # Очищаем состояние перед началом нового объявления
    await state.clear()

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
    current_state = await state.get_state()
    prev_state = await pop_state(state)

    if not prev_state:
        await callback.answer("Вы на первом шаге")
        return
    
    # Если возвращаемся с шага "preview" на шаг "фото" - очищаем фотографии и превью
    if current_state == AddAdvertisement.preview and prev_state == AddAdvertisement.photo:
        data = await state.get_data()

        preview_ids = data.get("preview_messages_ids", [])
        for msg_id in preview_ids:
            try:
                await callback.bot.delete_message(
                    chat_id=callback.message.chat.id, 
                    message_id=msg_id
                )
            except Exception:
                pass

        # Удаляем финальное сообщение с кнопками если есть
        try:
            final_msg_id = data.get("final_message_id")
            if final_msg_id:
                await callback.bot.delete_message(
                    chat_id=callback.message.chat.id,
                    message_id=final_msg_id
                )
        except Exception:
            pass

    # Если возвращаемся с шага "финиш" на шаг "фото" - очищаем фотографии
    ### TEMP COMMENTED ###
    # if current_state == AddAdvertisement.finish and prev_state == AddAdvertisement.photo:
    #     data = await state.get_data()

    #     preview_ids = data.get("preview_messages_ids", [])
    #     for msg_id in preview_ids:
    #         try:
    #             await callback.bot.delete_message(
    #                 chat_id=callback.message.chat.id, 
    #                 message_id=msg_id
    #             )
    #         except Exception:
    #             pass

        await state.update_data(
            media_group=[],
            media_messages_ids=[],
            preview_messages_ids=[],
            final_message_id=None
        )

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
    await render_description(callback.message, state)


@user_private_router.message(StateFilter(AddAdvertisement.description), F.text)
async def create_ad_add_description(message: types.Message, state: FSMContext, bot: Bot):
    await state.update_data(description=message.text)

    next_state = AddAdvertisement.price

    await push_state(state, next_state)
    await state.set_state(next_state)
    await render_price(message, state)


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
    await render_photo(message, state)



@user_private_router.message(
    StateFilter(AddAdvertisement.photo), 
    F.photo & ~F.media_group_id
)
async def add_photo(message: Message, state: FSMContext):
    data = await state.get_data()

    media_group = data.get("media_group", [])
    media_messages_ids = data.get("media_messages_ids", [])
    tmp_messages = data.get("tmp_messages", [])


    if len(media_group) >= MAX_PHOTOS:
        warn = await message.answer("Можно добавить не более 10 фотографий")

        tmp_messages.append(warn.message_id)
        await state.update_data(tmp_messages=tmp_messages)        

        await message.delete()

        return

    media_group.append(
        types.InputMediaPhoto(media=message.photo[-1].file_id)
    )
    media_messages_ids.append(message.message_id)

    await state.update_data(
        media_group=media_group,
        media_messages_ids=media_messages_ids,
        tmp_messages=tmp_messages
    )


@user_private_router.message(
    StateFilter(AddAdvertisement.photo), 
    F.media_group_id
)
async def add_media_group(message: Message, state: FSMContext, album: list[Message]):
    data = await state.get_data()
    media_group = data.get("media_group", [])
    media_messages_ids = data.get("media_messages_ids", [])

    free_slots = MAX_PHOTOS - len(media_group)

    if free_slots <= 0:
        await message.answer("Можно добавить не более 10 фотографий")

        for msg in album:
            await msg.delete()

        return

    for msg in album[:free_slots]:
        media_group.append(
            types.InputMediaPhoto(media=msg.photo[-1].file_id)
        )
        media_messages_ids.append(msg.message_id)

    for msg in album[free_slots:]:
        await msg.delete()

    if len(album) > free_slots:
        await message.answer(
            f"Добавлено только {free_slots} фото. Лимит — {MAX_PHOTOS}."
        )

    await state.update_data(
        media_group=media_group, 
        media_messages_ids=media_messages_ids
    )


@user_private_router.callback_query(
    StateFilter(AddAdvertisement.photo), 
    F.data == "cancel_ad"
)
async def cancel_on_photo_step(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    
    # Удаляем временные фотографии
    media_message_ids = data.get("media_messages_ids", [])
    if media_message_ids:
        await delete_media(
            bot=bot,
            chat_id=callback.message.chat.id,
            message_ids=media_message_ids
        )
    
    # Удаляем временные сообщения
    tmp_messages = data.get("tmp_messages", [])
    for msg_id in tmp_messages:
        try:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
        except Exception:
            pass

    await callback.answer("Добавление фотографий отменено")
    
    # Возвращаемся к шагу цены или показываем сообщение об отмене
    await callback.message.edit_text(
        "Добавление фотографий отменено.\n\nНажмите 'Отмена' для полной отмены объявления.",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="↩️ Назад к цене", callback_data="back_button"),
                ],
                [
                    types.InlineKeyboardButton(text="🚫 Отменить всё объявление", callback_data="cancel_ad_full"),
                ]
            ]
        )
    )
    
    # Очищаем данные о фотографиях
    await state.update_data(
        media_group=[],
        media_messages_ids=[],
        tmp_messages=[]
    )


@user_private_router.callback_query(
    StateFilter(AddAdvertisement.photo), 
    F.data == "cancel_ad_full"
)
async def cancel_full_ad_from_photo(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    
    # Удаляем все временные сообщения
    all_message_ids = (
        data.get("media_messages_ids", []) + 
        data.get("tmp_messages", [])
    )
    
    if all_message_ids:
        await delete_media(
            bot=bot,
            chat_id=callback.message.chat.id,
            message_ids=all_message_ids
        )

    await callback.answer("Объявление отменено")
    await callback.message.edit_text(
        "Создание объявления полностью отменено.\n", 
        reply_markup=single_button_kb(
            text="Создать новое объявление",
            callback_data="create_ad"
        )
    )

    await state.clear()


@user_private_router.callback_query(StateFilter(AddAdvertisement.photo), F.data == "photos_done")
async def photos_done(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()

    media_group = data.get("media_group", [])
    if not media_group:
        no_preview_message = await callback.message.answer("Нет фото для превью.")
        await callback.answer("Добавьте хотя бы одно фото")
        no_preview_message_id = no_preview_message.message_id
        tmp_messages = data.get("tmp_messages", [])
        tmp_messages.append(no_preview_message_id)
        await state.update_data(tmp_messages=tmp_messages)
        return
    
    await callback.answer("Фотографии сохранены!")
    
    # Удаляем старое wizard-сообщение
    await delete_old_wizard_message(state, bot)
    
    # Переходим на финальный шаг превью
    next_state = AddAdvertisement.preview

    await push_state(state, next_state)
    await state.set_state(next_state)

    category_key = data.get('category', '-')
    category_name = CATEGORIES.get(category_key, category_key)

    condition_key = data.get('condition', '-')
    condition_name = CONDITIONS.get(condition_key, condition_key)
    
    # Формируем полное превью объявления
    text_preview = (
        f"📌 <b>Название:</b> {data.get('name', '-')}\n"
        f"📂 <b>Категория:</b> {category_name}\n"
        f"🔧 <b>Состояние:</b> {condition_name}\n"
        f"📝 <b>Описание:</b> {data.get('description', '-')}\n"
        f"💰 <b>Цена:</b> {data.get('price', '-')} руб.\n"
        f"\n<b>Превью фотографий:</b>"
    )

    # Сначала отправляем текст превью
    preview_text_message = await bot.send_message(
        chat_id=callback.message.chat.id,
        text=text_preview,
        parse_mode="HTML"
    )

    # Затем отправляем фотографии как медиагруппу
    preview_messages = await bot.send_media_group(
        chat_id=callback.message.chat.id,
        media=media_group
    )

    preview_ids = [msg.message_id for msg in preview_messages]

    # Кнопки для финального шага
    final_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✅ Опубликовать", callback_data="publish_ad"),
                types.InlineKeyboardButton(text="↩️ Назад к фото", callback_data="back_to_photos"),
            ]
        ]
    )

    # Отправляем сообщение с кнопками действий
    final_message = await bot.send_message(
        chat_id=callback.message.chat.id,
        text="<b>Это будет выглядеть так в канале.</b>\n\nВсё верно? Нажмите 'Опубликовать' для размещения объявления.",
        parse_mode="HTML",
        reply_markup=final_kb
    )

    # Обновляем состояние
    await state.update_data(
        wizard_message_id=final_message.message_id,
        wizard_chat_id=final_message.chat.id,
        preview_messages_ids=[preview_text_message.message_id] + preview_ids,
        final_message_id=final_message.message_id
    )

    # Удаляем временные сообщения
    tmp_messages = data.get("tmp_messages", [])
    for msg_id in tmp_messages:
        try:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
        except Exception:
            pass
    await state.update_data(tmp_messages=[])
    

@user_private_router.callback_query(StateFilter(AddAdvertisement.preview), F.data == "back_to_photos")
async def back_to_photos(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()

    # Удаляем превью сообщения
    for msg_id in data.get("preview_messages_ids", []):
        try:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
        except Exception:
            pass

    # Удаляем финальное сообщение с кнопками
    try:
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=data["final_message_id"])
    except Exception:
        pass

    # Удаляем старое wizard-сообщение
    await delete_old_wizard_message(state, bot)

    # ВАЖНО: Очищаем старые фотографии перед возвратом на шаг фото
    await state.update_data(
        media_group=[],      # Очищаем список медиа
        media_messages_ids=[],  # Очищаем ID сообщений с фото
        preview_messages_ids=[],  # Очищаем список ID превью
        final_message_id=None  # Очищаем final_message_id
    )

    # Также нужно очистить стек состояний, чтобы корректно работала кнопка "Назад"
    # Извлекаем текущее состояние из стека (preview)
    await pop_state(state)
    # Затем возвращаемся к photo (которое должно остаться в стеке)

    # Возвращаемся на шаг фото
    await state.set_state(AddAdvertisement.photo)

    # Возвращаемся на шаг фото
    ### TEMP COMMENTED ###
    # prev_state = AddAdvertisement.photo
    # await state.set_state(prev_state)
    await render_photo(callback.message, state)
    await callback.answer("Вы вернулись к редактированию фотографий")


@user_private_router.callback_query(StateFilter(AddAdvertisement.finish), F.data == "edit_photos")
async def edit_photos(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()

    # Удаляем превью (текст + превью медиа)
    for msg_id in data.get("preview_messages_ids", []):
        try:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
        except Exception:
            pass

    try:
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=data["wizard_message_id"])
    except Exception:
        pass

    # Очищаем фотографии
    await state.update_data(
        media_group=[],  # Очищаем список медиа
        media_messages_ids=[],  # Очищаем ID сообщений с фото
    )
        
    # Возвращаемся на шаг фото
    await state.set_state(AddAdvertisement.photo)
    await render_photo(callback.message, state)
    await callback.answer("Вы вернулись к редактированию фотографий")


@user_private_router.callback_query(
    StateFilter(AddAdvertisement.preview), F.data == "publish_ad"
)
async def create_ad_publish(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    
    # Формируем описание для публикации
    post_caption = (
        f"🏷️ <b>{data.get('name', '-')}</b>\n\n"
        f"📂 Категория: {data.get('category', '-')}\n"
        f"🔧 Состояние: {data.get('condition', '-')}\n"
        f"💰 Цена: {data.get('price', '-')} руб.\n\n"
        f"📝 Описание:\n{data.get('description', '-')}\n\n"
        f"👤 Контакт: @{callback.from_user.username or 'Написать в ЛС'}"
    )
    
    # Копируем медиагруппу и добавляем подпись к первой фотографии
    media_group_for_post = []
    for i, media in enumerate(data.get("media_group", [])):
        media_copy = types.InputMediaPhoto(media=media.media)
        if i == 0:  # Только к первой фотографии добавляем подпись
            media_copy.caption = post_caption
            media_copy.parse_mode = "HTML"
        media_group_for_post.append(media_copy)
    
    # Отправляем объявление в канал
    try:
        sended_messages = await bot.send_media_group(
            chat_id=ADS_CHAT_ID, 
            media=media_group_for_post
        )
        
        # Получаем ссылку на пост
        first_message_id = sended_messages[0].message_id
        chat_url = f"https://t.me/{ADS_CHAT_NAME}/{first_message_id}"
        
        await callback.answer("Спасибо!\nОбъявление успешно опубликовано!")
        
        # Обновляем сообщение с результатом
        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=(
                "✅ <b>Объявление успешно опубликовано!</b>\n\n"
                f"Ссылка на объявление:\n{chat_url}\n\n"
                "Спасибо за использование нашего бота! 🎉"
            ),
            parse_mode="HTML",
            reply_markup=single_button_kb(
                text="Создать еще одно!",
                callback_data="create_ad"
            )
        )
        
    except Exception as e:
        await callback.answer("Ошибка при публикации объявления")
        await callback.message.edit_text(
            "❌ <b>Произошла ошибка при публикации объявления.</b>\n\n"
            "Пожалуйста, попробуйте позже или обратитесь к администратору.",
            parse_mode="HTML"
        )
        print(f"Ошибка публикации: {e}")
        return
    
    # Очищаем временные файлы и состояние
    await delete_media(
        bot=bot,
        chat_id=callback.message.chat.id,
        message_ids=(
            data.get("media_messages_ids", []) + 
            data.get("tmp_messages", [])
        )
    )
    
    # Удаляем превью сообщения
    for msg_id in data.get("preview_messages_ids", []):
        try:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
        except Exception:
            pass

    await state.clear()


@user_private_router.callback_query(
    StateFilter(AddAdvertisement.preview), F.data == "cancel_ad"
)
async def create_ad_cancel(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()

    # Удаляем превью сообщения
    for msg_id in data.get("preview_messages_ids", []):
        try:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
        except Exception:
            pass

    # Удаляем временные фотографии
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

    # Очищаем все данные
    await state.clear()
