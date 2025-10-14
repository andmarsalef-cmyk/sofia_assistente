import os
from dotenv import load_dotenv
from openai import OpenAI

# Cargar variables
load_dotenv("sofia.env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print("TELEGRAM_TOKEN:", "OK" if TELEGRAM_TOKEN else "FALTA")
print("OPENAI_API_KEY:", "OK" if OPENAI_API_KEY else "FALTA")

# Probar conexión a OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)
response = client.models.list()
print("✅ Conectado. Modelos disponibles:", [m.id for m in response.data[:3]])
