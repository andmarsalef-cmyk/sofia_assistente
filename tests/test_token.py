from dotenv import load_dotenv
import os
import asyncio
from telegram import Bot

# Cargar variables de entorno desde sofia.env
load_dotenv("sofia.env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
print("DEBUG -> TELEGRAM_TOKEN:", TELEGRAM_TOKEN)

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    try:
        me = await bot.get_me()  # Intenta obtener info del bot
        print("✅ Token válido. Bot info:")
        print("  Nombre:", me.first_name)
        print("  Username:", me.username)
        print("  ID:", me.id)
    except Exception as e:
        print("❌ Token inválido o no autorizado:", e)

# Ejecutar la prueba
asyncio.run(main())
