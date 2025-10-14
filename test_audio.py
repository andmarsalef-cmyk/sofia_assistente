import os
from dotenv import load_dotenv
from openai import OpenAI

# 1️⃣ Cargar la clave desde .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 2️⃣ Ruta del archivo de audio (sin espacios)
AUDIO_PATH = "prueba_audio.m4a"

# 3️⃣ Transcribir con Whisper (nuevo SDK)
try:
    with open(AUDIO_PATH, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        print(f"📝 Transcripción: {transcript.text}")
except Exception as e:
    print(f"⚠️ Error transcribiendo audio: {e}")
