import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

load_dotenv("sofia.env")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def test_token():
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        bot_info = await bot.get_me()
        print(f"Token válido. Bot name: {bot_info.username}")
    except Exception as e:
        print(f"Error con el token: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_token())
