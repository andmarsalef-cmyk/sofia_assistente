import os
from dotenv import load_dotenv
from sofia_telegram import verificar_token

# Cargar variables de entorno
load_dotenv("sofia.env")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

print("Probando verificación del token...")
if verificar_token(TELEGRAM_TOKEN):
    print("✅ El token funciona correctamente.")
else:
    print("❌ El token NO es válido.")
