from aiogram.fsm.state import State, StatesGroup


class AddAdvertisement(StatesGroup):
    name = State()
    category = State()
    condition = State()
    price = State()
    description = State()
    photo = State()
    preview = State()
    finish = State()

    texts = {
        "AddAdvertisement:name": "Введите название для объявления заново:",
        "AddAdvertisement:category": "Выберите категорию для объявления заново:",
        "AddAdvertisement:condition": "Выберите состояние для объявления заново:",
        "AddAdvertisement:price": "Введите цену для объявления заново:",
        "AddAdvertisement:description": "Введите описание для объявления заново:",
        "AddAdvertisement:photo": "Отправьте фото для объявления заново:",
    }
