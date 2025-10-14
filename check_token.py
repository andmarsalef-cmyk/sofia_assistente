import asyncio
from telegram import Bot

# 🔹 Pega aquí el token que quieras probar
TOKEN = "8400542436:AAE4kZ40qJKigZNEWDwrfuEVIsvGpSfWWew"

async def check():
    try:
        bot = Bot(TOKEN)
        me = await bot.get_me()
        print("✅ Token válido.")
        print("🤖 Bot username:", me.username)
        print("🆔 Bot ID:", me.id)
    except Exception as e:
        print("❌ Token inválido o no autorizado:", e)

if __name__ == "__main__":
    asyncio.run(check())
