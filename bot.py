
import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)

from database import init_db, save_user, get_user
from prayer import get_prayer_times
from reminders import reminder_loop

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

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
        "🇺🇿 O‘zbekiston bo‘yicha namoz vaqtlari.\n"
        "🌙 Ramazon taqvimi.\n"
        "🔔 Avtomatik namoz eslatmalari.\n\n"
        "Boshlash uchun shahringizni tanlang.",
        reply_markup=menu
    )


@dp.message(F.text == "📍 Shaharni tanlash")
async def choose_city(message: Message, state: FSMContext):
    await state.set_state(CityForm.waiting)

    await message.answer(
        "📍 Shahringizni quyidagi shaklda yuboring:\n\n"
        "Yaypan, Farg‘ona viloyati\n\n"
        "Masalan:\n"
        "Toshkent, Toshkent shahri",
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message(CityForm.waiting)
async def save_city(message: Message, state: FSMContext):
    if not message.text or "," not in message.text:
        await message.answer(
            "❌ Iltimos, shahar va viloyatni vergul bilan yozing."
        )
        return

    city, region = message.text.split(",", 1)

    city = city.strip()
    region = region.strip()

    try:
        times = await get_prayer_times(city, region)

        await save_user(
            message.from_user.id,
            region,
            city
        )

        await state.clear()

        await message.answer(
            f"✅ Hududingiz saqlandi!\n\n"
            f"📍 {city}, {region}\n\n"
            f"🕌 Bomdod: {times['Bomdod']}\n"
            f"☀️ Quyosh: {times['Quyosh']}\n"
            f"🕌 Peshin: {times['Peshin']}\n"
            f"🕌 Asr: {times['Asr']}\n"
            f"🌅 Shom: {times['Shom']}\n"
            f"🌙 Xufton: {times['Xufton']}",
            reply_markup=menu
        )

    except Exception:
        logging.exception("Shaharni tekshirish xatosi")

        await message.answer(
            "❌ Bu hudud bo‘yicha vaqtlarni olishda xatolik.\n\n"
            "Shahar nomini tekshirib qayta yuboring."
        )


@dp.message(F.text == "🕌 Namoz vaqtlari")
async def prayer(message: Message):
    user = await get_user(message.from_user.id)

    if not user or not user[1] or not user[2]:
        await message.answer(
            "📍 Avval shahringizni tanlang.",
            reply_markup=menu
        )
        return

    try:
        times = await get_prayer_times(user[2], user[1])

        text = "🕌 BUGUNGI NAMOZ VAQTLARI\n\n"

        text += f"📍 {user[2]}, {user[1]}\n\n"

        for name, time in times.items():
            text += f"• {name}: {time}\n"

        await message.answer(text)

    except Exception:
        logging.exception("Namoz vaqti xatosi")

        await message.answer(
            "Namoz vaqtlarini olishda xatolik yuz berdi."
        )


@dp.message(F.text == "🔔 Eslatmalar")
async def reminders(message: Message):
    user = await get_user(message.from_user.id)

    if not user or not user[1] or not user[2]:
        await message.answer(
            "Avval shahringizni tanlang."
        )
        return

    await message.answer(
        "🔔 NAMOZ ESLATMALARI\n\n"
        "✅ 15 daqiqa oldin xabar\n"
        "✅ Namoz vaqti kirganda xabar\n"
        "✅ Barcha 5 mahal namoz\n\n"
        "Eslatmalar avtomatik ishlaydi."
    )


@dp.message(F.text == "🌙 Ramazon taqvimi")
async def ramadan(message: Message):
    user = await get_user(message.from_user.id)

    if not user or not user[1] or not user[2]:
        await message.answer(
            "📍 Avval shahringizni tanlang."
        )
        return

    await message.answer(
        "🌙 RAMAZON TAQVIMI 2027\n\n"
        "📍 Hududingiz: "
        f"{user[2]}, {user[1]}\n\n"
        "Saharlik va iftorlikning rasmiy "
        "vaqtlarini jadval e'lon qilingach qo‘shamiz."
    )


@dp.message()
async def unknown(message: Message):
    await message.answer(
        "Kerakli bo‘limni menyudan tanlang 👇",
        reply_markup=menu
    )


async def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN topilmadi!")

    await init_db()

    reminder_task = asyncio.create_task(
        reminder_loop(bot)
    )

    logging.info("NAMOZ VAQTI UZ ishga tushmoqda...")

    try:
        await dp.start_polling(bot)

    finally:
        reminder_task.cancel()

        try:
            await reminder_task
        except asyncio.CancelledError:
            pass

        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
