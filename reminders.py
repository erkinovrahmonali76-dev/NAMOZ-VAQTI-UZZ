
import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import aiosqlite
from database import get_all_users
from prayer import get_prayer_times

TZ = ZoneInfo("Asia/Tashkent")
CACHE = {}

async def reminder_loop(bot):
    logging.info("Namoz eslatmalari ishga tushdi")

    async with aiosqlite.connect("namoz.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sent_reminders (
                user_id INTEGER,
                prayer_date TEXT,
                prayer_name TEXT,
                reminder_type TEXT,
                PRIMARY KEY (
                    user_id, prayer_date,
                    prayer_name, reminder_type
                )
            )
        """)
        await db.commit()

    while True:
        try:
            now = datetime.now(TZ)
            today = now.strftime("%Y-%m-%d")
            users = await get_all_users()

            for user in users:
                user_id, region, city = user[0], user[1], user[2]
                minutes = user[3] or 15
                enabled = user[4]

                if not enabled or not city or not region:
                    continue

                key = (city, region, today)

                try:
                    if key not in CACHE or (
                        now - CACHE[key][0]
                    ).total_seconds() > 300:
                        times = await get_prayer_times(city, region)
                        CACHE[key] = (now, times)
                    else:
                        times = CACHE[key][1]

                    for prayer_name in (
                        "Bomdod", "Peshin", "Asr", "Shom", "Xufton"
                    ):
                        prayer_time = datetime.strptime(
                            times[prayer_name], "%H:%M"
                        ).time()

                        target = datetime.combine(
                            now.date(), prayer_time, tzinfo=TZ
                        )

                        events = [
                            ("before", target - timedelta(minutes=minutes)),
                            ("at", target)
                        ]

                        for event_type, event_time in events:
                            if now.strftime("%H:%M") != event_time.strftime("%H:%M"):
                                continue

                            async with aiosqlite.connect("namoz.db") as db:
                                cursor = await db.execute("""
                                    INSERT OR IGNORE INTO sent_reminders
                                    VALUES (?, ?, ?, ?)
                                """, (
                                    user_id, today,
                                    prayer_name, event_type
                                ))
                                await db.commit()

                                if cursor.rowcount == 0:
                                    continue

                            if event_type == "before":
                                message = (
                                    f"🔔 {prayer_name} namoziga "
                                    f"{minutes} daqiqa qoldi!\n\n"
                                    f"Namoz vaqti: {times[prayer_name]}"
                                )
                            else:
                                message = (
                                    f"🕌 {prayer_name} namozi vaqti kirdi!\n\n"
                                    "Alloh ibodatlaringizni qabul qilsin. 🤲"
                                )

                            await bot.send_message(user_id, message)

                except Exception:
                    logging.exception(
                        "Foydalanuvchi %s uchun eslatma xatosi", user_id
                    )

        except Exception:
            logging.exception("Eslatma tizimida xatolik")

        await asyncio.sleep(30)
