# ==============================
# 🔹 test_chat.py
# ==============================
import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ==============================
# 🔹 Cargar variables de entorno
# ==============================
load_dotenv("sofia.env")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")  # tu chat_id de Telegram

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("❌ TELEGRAM_TOKEN o CHAT_ID faltante en sofia.env")

bot = Bot(token=TELEGRAM_TOKEN)

# ==============================
# 🔹 Función para enviar mensajes
# ==============================
async def enviar_mensajes():
    mensajes = [
        "Hola Sofía, ¿cómo estás?",
        "¿Cuál es la capital de Francia?",
        "Dime un chiste corto",
        "Explícame qué es la IA",
        "Gracias Sofía"
    ]
    for msg in mensajes:
        print("📤 Enviando:", msg)
        await bot.send_message(chat_id=CHAT_ID, text=msg)
        await asyncio.sleep(1)  # breve pausa para no saturar

# ==============================
# 🔹 Main
# ==============================
async def main():
    print("🚀 Test chat iniciado...")
    await enviar_mensajes()
    print("✅ Mensajes enviados correctamente.")

if __name__ == "__main__":
    asyncio.run(main())
