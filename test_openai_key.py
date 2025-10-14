import os
from dotenv import load_dotenv
from openai import OpenAI

# Cargar variables de entorno
load_dotenv("sofia.env")
api_key = os.getenv("OPENAI_API_KEY")

print("DEBUG -> OPENAI_API_KEY:", api_key[:8], "...")  # muestra solo inicio

client = OpenAI(api_key=api_key)

try:
    # Pequeña prueba de chat
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Eres un probador de API."},
            {"role": "user", "content": "Respóndeme solo con 'OK'."}
        ],
        max_tokens=5
    )
    print("✅ API Key válida, respuesta:", resp.choices[0].message.content)
except Exception as e:
    print("❌ Error con la API Key:", e)
