import logging
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

class Form(StatesGroup):
    waiting_for_service = State()
    waiting_for_car = State()
    waiting_for_contact = State()

services = [
    "Химчистка", "Полировка\керамика", "Бронепленка", "Тонировка",
    "Удаление вмятин", "Реставрация кожи", "Цветная пленка", "Бронь лобового",
    "Шлифовка фар", "Покраска дисков", "Защита салона", "Другой вопрос" 
]
service_keyboard = InlineKeyboardMarkup(row_width=2)
for s in services:
    service_keyboard.insert(InlineKeyboardButton(s, callback_data=s))

@dp.message_handler(commands="start")
async def start_handler(message: types.Message):
    welcome_text = (
        "Здравствуйте! Добро пожаловать в R&A Detailing Studio.\n"
        "Мы предлагаем широкий спектр детейлинг-услуг премиум-класса.\n\n"
        "Пожалуйста, выберите услугу из списка ниже, чтобы начать запись."
    )
    await message.answer(welcome_text, reply_markup=service_keyboard)
    await Form.waiting_for_service.set()

@dp.callback_query_handler(state=Form.waiting_for_service)
async def service_chosen(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(service=call.data)
    await call.message.edit_reply_markup()
    await call.message.answer("Отлично! Теперь введите марку и модель вашего автомобиля:")
    await Form.waiting_for_car.set()

@dp.message_handler(state=Form.waiting_for_car)
async def car_received(message: types.Message, state: FSMContext):
    await state.update_data(car=message.text)
    await message.answer(
        "Пожалуйста, введите ваше имя и номер телефона в одном сообщении через запятую или пробел.\n"
        "Например: Иван, +7 999 123 45 67"
    )
    await Form.waiting_for_contact.set()

@dp.message_handler(state=Form.waiting_for_contact)
async def contact_received(message: types.Message, state: FSMContext):
    contact_text = message.text.strip()
    if ',' in contact_text:
        name, phone = map(str.strip, contact_text.split(',', 1))
    else:
        parts = contact_text.split(maxsplit=1)
        if len(parts) == 2:
            name, phone = parts
        else:
            await message.answer("Пожалуйста, введите имя и телефон корректно, разделяя их запятой или пробелом.")
            return

    await state.update_data(name=name, phone=phone)
    data = await state.get_data()
    await state.finish()

    text = (
        "📩 *Новая заявка на детейлинг*\n\n"
        f"🛠 Услуга: {data['service']}\n"
        f"🚗 Авто: {data['car']}\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}"
    )

    await message.answer("Спасибо! Ваша заявка принята. Мы свяжемся с вами в ближайшее время.")

    try:
        await bot.send_message(ADMIN_ID, text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Ошибка отправки заявки администратору: {e}")
        await message.answer("Произошла ошибка при отправке заявки администратору.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)