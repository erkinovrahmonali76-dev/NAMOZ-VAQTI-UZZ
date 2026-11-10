
import aiosqlite

DB_NAME = "namoz.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            region TEXT,
            city TEXT,
            reminder_minutes INTEGER DEFAULT 15,
            reminders_enabled INTEGER DEFAULT 1
        )
        """)
        await db.commit()

async def save_user(user_id, region=None, city=None):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        INSERT INTO users (user_id, region, city)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
        region=COALESCE(excluded.region, users.region),
        city=COALESCE(excluded.city, users.city)
        """, (user_id, region, city))
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )
        return await cursor.fetchone()

async def get_all_users():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM users")
        return await cursor.fetchall()
