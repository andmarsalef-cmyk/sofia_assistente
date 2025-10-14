import asyncio
from telegram import Bot

TOKEN = "8197202364:AAHyD9STma6WJfoiJHJ5AJRvjxXi957BhA"

async def main():
    bot = Bot(token=TOKEN)
    try:
        user = await bot.get_me()
        print("✅ Token válido. Bot detectado:", user.username)
    except Exception as e:
        print("❌ Token inválido o no autorizado:", e)

asyncio.run(main())
