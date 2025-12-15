import asyncio
from telegram import Bot

# 🔹 Pega aquí el token que quieras probar
TOKEN = "8587346244:AAGyt2KLBozmaO9r_F2Cj-3QDDDMTCZI3XE"

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
