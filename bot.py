
import os
import asyncio
import logging

from aiohttp import web

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)

from database import init_db, save_user, get_user
from prayer import get_prayer_times
from reminders import reminder_loop


# ==============================
# SOZLAMALAR
# ==============================

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
PORT = int(os.getenv("PORT", "10000"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

if not TOKEN:
    raise RuntimeError("BOT_TOKEN Render Environment'da topilmadi!")

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ==============================
# HOLATLAR
# ==============================

class CityForm(StatesGroup):
    waiting = State()


# ==============================
# MENYU
# ==============================

menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🕌 Namoz vaqtlari")],
        [KeyboardButton(text="🌙 Ramazon taqvimi")],
        [KeyboardButton(text="🔔 Eslatmalar")],
        [KeyboardButton(text="📍 Shaharni tanlash")],
    ],
    resize_keyboard=True,
)


# ==============================
# START
# ==============================

@dp.message(CommandStart())
async def start(message: Message):
    await save_user(message.from_user.id)

    await message.answer(
        "🕌 NAMOZ VAQTI UZ botiga xush kelibsiz!\n\n"
        "🇺🇿 O‘zbekiston bo‘yicha namoz vaqtlari.\n"
        "🌙 Ramazon taqvimi.\n"
        "🔔 Namoz eslatmalari.\n\n"
        "Boshlash uchun shahringizni tanlang.",
        reply_markup=menu,
    )


# ==============================
# SHAHAR TANLASH
# ==============================

@dp.message(F.text == "📍 Shaharni tanlash")
async def choose_city(message: Message, state: FSMContext):
    await state.set_state(CityForm.waiting)

    await message.answer(
        "📍 Shahringizni quyidagi shaklda yuboring:\n\n"
        "Yaypan, Farg‘ona viloyati\n\n"
        "Masalan:\n"
        "Toshkent, Toshkent shahri",
        reply_markup=ReplyKeyboardRemove(),
    )


@dp.message(CityForm.waiting)
async def save_city(message: Message, state: FSMContext):
    if not message.text or "," not in message.text:
        await message.answer(
            "❌ Shahar va viloyatni vergul bilan yozing.\n"
            "Masalan: Yaypan, Farg‘ona viloyati"
        )
        return

    city, region = message.text.split(",", 1)

    city = city.strip()
    region = region.strip()

    await message.answer("⏳ Namoz vaqtlari tekshirilmoqda...")

    try:
        times = await get_prayer_times(city, region)

        await save_user(
            message.from_user.id,
            region,
            city,
        )

        await state.clear()

        text = (
            "✅ Hududingiz saqlandi!\n\n"
            f"📍 {city}, {region}\n\n"
        )

        for name, value in times.items():
            text += f"• {name}: {value}\n"

        await message.answer(text, reply_markup=menu)

    except Exception:
        logging.exception("Shaharni tekshirish xatosi")

        await message.answer(
            "❌ Hozir namoz vaqtlarini olishda muammo bor.\n\n"
            "Internet yoki vaqtlar xizmatida vaqtinchalik "
            "nosozlik bo‘lishi mumkin.\n"
            "Birozdan keyin qayta urinib ko‘ring.",
            reply_markup=menu,
        )


# ==============================
# NAMOZ VAQTLARI
# ==============================

@dp.message(F.text == "🕌 Namoz vaqtlari")
async def prayer(message: Message):
    user = await get_user(message.from_user.id)

    if not user or not user[1] or not user[2]:
        await message.answer(
            "📍 Avval shahringizni tanlang.",
            reply_markup=menu,
        )
        return

    try:
        times = await get_prayer_times(user[2], user[1])

        text = (
            "🕌 BUGUNGI NAMOZ VAQTLARI\n\n"
            f"📍 {user[2]}, {user[1]}\n\n"
        )

        for name, value in times.items():
            text += f"• {name}: {value}\n"

        await message.answer(text, reply_markup=menu)

    except Exception:
        logging.exception("Namoz vaqti xatosi")

        await message.answer(
            "❌ Namoz vaqtlarini olishda vaqtinchalik xatolik.\n"
            "Birozdan keyin qayta urinib ko‘ring."
        )


# ==============================
# ESLATMALAR
# ==============================

@dp.message(F.text == "🔔 Eslatmalar")
async def reminders(message: Message):
    user = await get_user(message.from_user.id)

    if not user or not user[1] or not user[2]:
        await message.answer(
            "📍 Avval shahringizni tanlang.",
            reply_markup=menu,
        )
        return

    await message.answer(
        "🔔 NAMOZ ESLATMALARI\n\n"
        "⏰ 15 daqiqa oldin xabar\n"
        "🕌 Namoz vaqti kirganda xabar\n"
        "✅ Barcha 5 mahal namoz\n\n"
        "Eslatmalar sozlamalari faol bo‘lishi kerak.",
        reply_markup=menu,
    )


# ==============================
# RAMAZON
# ==============================

@dp.message(F.text == "🌙 Ramazon taqvimi")
async def ramadan(message: Message):
    user = await get_user(message.from_user.id)

    if not user or not user[1] or not user[2]:
        await message.answer(
            "📍 Avval shahringizni tanlang.",
            reply_markup=menu,
        )
        return

    await message.answer(
        "🌙 RAMAZON TAQVIMI 2027\n\n"
        f"📍 Hududingiz: {user[2]}, {user[1]}\n\n"
        "Rasmiy saharlik va iftorlik jadvali "
        "tasdiqlangach shu bo‘limga qo‘shiladi.",
        reply_markup=menu,
    )


# ==============================
# NOMA'LUM XABAR
# ==============================

@dp.message()
async def unknown(message: Message):
    await message.answer(
        "Kerakli bo‘limni menyudan tanlang 👇",
        reply_markup=menu,
    )


# ==============================
# WEBHOOK
# ==============================

async def home(request):
    return web.Response(
        text="NAMOZ VAQTI UZ is running!"
    )


async def telegram_webhook(request):
    if WEBHOOK_SECRET:
        received_secret = request.headers.get(
            "X-Telegram-Bot-Api-Secret-Token"
        )

        if received_secret != WEBHOOK_SECRET:
            raise web.HTTPUnauthorized()

    try:
        data = await request.json()

        update = Update.model_validate(
            data,
            context={"bot": bot},
        )

        await dp.feed_update(bot, update)

        return web.Response(text="OK")

    except Exception:
        logging.exception("Webhook update xatosi")
        raise web.HTTPInternalServerError()


# ==============================
# SERVER ISHGA TUSHISHI
# ==============================

async def on_startup(app):
    await init_db()

    hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME")

    if not hostname:
        raise RuntimeError(
            "RENDER_EXTERNAL_HOSTNAME topilmadi!"
        )

    webhook_url = (
        f"https://{hostname}/telegram-webhook"
    )

    await bot.set_webhook(
        webhook_url,
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=False,
    )

    app["reminder_task"] = asyncio.create_task(
        reminder_loop(bot)
    )

    logging.info("NAMOZ VAQTI UZ ishga tushdi!")


async def on_cleanup(app):
    task = app.get("reminder_task")

    if task:
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

    await bot.delete_webhook()
    await bot.session.close()


# ==============================
# MAIN
# ==============================

def main():
    app = web.Application()

    app.router.add_get("/", home)

    app.router.add_post(
        "/telegram-webhook",
        telegram_webhook,
    )

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    web.run_app(
        app,
        host="0.0.0.0",
        port=PORT,
    )


if __name__ == "__main__":
    main()
