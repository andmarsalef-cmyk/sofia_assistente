from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv

# 🔹 Cargar variables de entorno
load_dotenv("sofia.env")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"Tu chat ID es: {chat_id}")
    print(f"DEBUG -> Chat ID detectado: {chat_id}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("🤖 Envía /start a tu bot para obtener el chat ID...")
    app.run_polling()

if __name__ == "__main__":
    main()
