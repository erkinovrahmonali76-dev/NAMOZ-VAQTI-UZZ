
import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from database import init_db, save_user, get_user
from prayer import get_prayer_times

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()


class CityForm(StatesGroup):
    waiting = State()


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
    await save_user(message.from_user.id)
    await message.answer(
        "🕌 NAMOZ VAQTI UZ botiga xush kelibsiz!\n\n"
        "Namoz vaqtlarini ko‘rish uchun shahringizni tanlang.",
        reply_markup=menu
    )


@dp.message(F.text == "📍 Shaharni tanlash")
async def choose_city(message: Message, state: FSMContext):
    await state.set_state(CityForm.waiting)
    await message.answer(
        "Viloyat va shaharni shu ko‘rinishda yuboring:\n\n"
        "Yaypan, Farg‘ona viloyati"
    )


@dp.message(CityForm.waiting)
async def save_city(message: Message, state: FSMContext):
    try:
        city, region = message.text.split(",", 1)
        await save_user(
            message.from_user.id,
            region.strip(),
            city.strip()
        )
        await state.clear()
        await message.answer(
            f"✅ Hududingiz saqlandi: {city.strip()}, {region.strip()}",
            reply_markup=menu
        )
    except ValueError:
        await message.answer(
            "Iltimos, shunday yozing:\nYaypan, Farg‘ona viloyati"
        )


@dp.message(F.text == "🕌 Namoz vaqtlari")
async def prayer(message: Message):
    user = await get_user(message.from_user.id)

    if not user or not user[1] or not user[2]:
        await message.answer("Avval 📍 Shaharni tanlash tugmasini bosing.")
        return

    try:
        times = await get_prayer_times(user[2], user[1])
        text = "🕌 BUGUNGI NAMOZ VAQTLARI\n\n"

        for name, time in times.items():
            text += f"• {name}: {time}\n"

        await message.answer(text)

    except Exception:
        logging.exception("Prayer API error")
        await message.answer(
            "Namoz vaqtlarini olishda xatolik. Keyinroq urinib ko‘ring."
        )


@dp.message(F.text == "🔔 Eslatmalar")
async def reminders(message: Message):
    await message.answer(
        "🔔 Eslatma sozlamalari:\n\n"
        "• 15 daqiqa oldin\n"
        "• Barcha 5 mahal namoz\n"
        "• Namoz vaqti kirganda ham xabar\n\n"
        "Avtomatik eslatmalar keyingi bosqichda ulanadi."
    )


@dp.message(F.text == "🌙 Ramazon taqvimi")
async def ramadan(message: Message):
    await message.answer(
        "🌙 RAMAZON 2027\n\n"
        "Rasmiy taqvim e’lon qilingach saharlik "
        "va iftorlik vaqtlarini ko‘rsatamiz."
    )


async def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN topilmadi!")

    await init_db()

    reminder_task = asyncio.create_task(reminder_loop(bot))

    try:
        await dp.start_polling(bot)
    finally:
        reminder_task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
