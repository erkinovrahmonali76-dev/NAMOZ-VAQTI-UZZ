
import aiohttp
from datetime import datetime
from zoneinfo import ZoneInfo

UZ_TZ = ZoneInfo("Asia/Tashkent")
API_URL = "https://api.aladhan.com/v1/timingsByCity"

async def get_prayer_times(city, region=""):
    # Shahar va viloyat nomlarini ajratish
    city = city.strip()
    region = region.strip()

    if "," in city and not region:
        parts = city.split(",", 1)
        city = parts[0].strip()
        region = parts[1].strip()

    now = datetime.now(UZ_TZ)
    date = now.strftime("%d-%m-%Y")

    params = {
        "city": city,
        "country": "Uzbekistan",
        "state": region,
        "school": 1
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{API_URL}/{date}",
            params=params,
            timeout=aiohttp.ClientTimeout(total=20)
        ) as response:
            response.raise_for_status()
            result = await response.json()

    if result.get("code") != 200:
        raise ValueError("Namoz vaqtlarini olishda xatolik")

    timings = result["data"]["timings"]

    return {
        "Bomdod": timings["Fajr"][:5],
        "Quyosh": timings["Sunrise"][:5],
        "Peshin": timings["Dhuhr"][:5],
        "Asr": timings["Asr"][:5],
        "Shom": timings["Maghrib"][:5],
        "Xufton": timings["Isha"][:5],
    }
