import os
from dotenv import load_dotenv
from telegram import Bot
import asyncio

# 🔹 Cargar variables de entorno
load_dotenv("sofia.env")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("❌ TELEGRAM_TOKEN o CHAT_ID faltante en sofia.env")

bot = Bot(token=TELEGRAM_TOKEN)

# 🔹 Mensajes de prueba
mensajes = [
    "Hola Sofía, ¿cómo estás?",
    "Dime un chiste corto",
    "Explícame qué es la inteligencia artificial",
    "Gracias Sofía"
]

async def enviar_mensajes():
    for msg in mensajes:
        print(f"📤 Enviando: {msg}")
        await bot.send_message(chat_id=CHAT_ID, text=msg)
        await asyncio.sleep(2)  # espera para que el bot responda

async def main():
    await enviar_mensajes()

if __name__ == "__main__":
    asyncio.run(main())
