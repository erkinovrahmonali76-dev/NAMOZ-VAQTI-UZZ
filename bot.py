
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🕌 Namoz vaqtlari")],
        [KeyboardButton(text="🌙 Ramazon taqvimi")],
        [KeyboardButton(text="🔔 Eslatmalar")],
        [KeyboardButton(text="📍 Shaharni tanlash")]
    ],
    resize_keyboard=True
)

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "🕌 NAMOZ VAQTI UZ botiga xush kelibsiz!\n\n"
        "O‘zbekiston bo‘yicha namoz vaqtlari va "
        "Ramazon taqvimini kuzatib boring.",
        reply_markup=menu
    )

@dp.message(lambda message: message.text == "🔔 Eslatmalar")
async def reminders(message: Message):
    await message.answer(
        "🔔 Standart eslatmalar:\n\n"
        "• 15 daqiqa oldin\n"
        "• Barcha 5 mahal namoz\n"
        "• Namoz vaqti kirganda\n\n"
        "Tez orada sozlamalarni boshqarish imkoniyati qo‘shiladi."
    )

@dp.message(lambda message: message.text == "🕌 Namoz vaqtlari")
async def prayer(message: Message):
    await message.answer(
        "🕌 Namoz vaqtlarini ko‘rish uchun avval shahringizni tanlang."
    )

@dp.message(lambda message: message.text == "🌙 Ramazon taqvimi")
async def ramadan(message: Message):
    await message.answer(
        "🌙 2027-yil Ramazon taqvimi.\n"
        "Rasmiy jadval e'lon qilingach yangilanadi."
    )

@dp.message(lambda message: message.text == "📍 Shaharni tanlash")
async def city(message: Message):
    await message.answer(
        "📍 Hozircha shahar tanlash funksiyasi ishlab chiqilmoqda."
    )

async def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN topilmadi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
