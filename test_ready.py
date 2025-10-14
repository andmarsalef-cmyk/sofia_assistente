# ==============================
# 🔹 test_read.py
# ==============================
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
import os
from openai import OpenAI

# 🔹 Cargar variables de entorno
load_dotenv("sofia.env")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print("DEBUG -> Variables cargadas")
print("DEBUG -> EMAIL_USER:", EMAIL_USER)
print("DEBUG -> EMAIL_PASS:", "****" if EMAIL_PASS else "No cargada")

# 🔹 Cliente OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

def clasificar_correo(asunto, remitente, cuerpo):
    prompt = f"""
    Eres un asistente que organiza correos.
    Clasifica el siguiente correo en una de estas categorías:
    - Personal
    - Trabajo
    - Notificación
    - Publicidad
    - Seguridad
    - Otro

    📩 Asunto: {asunto}
    👤 Remitente: {remitente}
    📝 Cuerpo: {cuerpo[:200]}...

    Responde SOLO con la categoría más adecuada.
    """
    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content.strip()

# 🔹 Conectar con Gmail IMAP
imap = imaplib.IMAP4_SSL("imap.gmail.com")
imap.login(EMAIL_USER, EMAIL_PASS)
imap.select("inbox")

# Buscar últimos 5 correos
status, messages = imap.search(None, "ALL")
email_ids = messages[0].split()[-5:]

for num in email_ids:
    _, msg_data = imap.fetch(num, "(RFC822)")
    raw_email = msg_data[0][1]
    msg = email.message_from_bytes(raw_email)

    asunto, encoding = decode_header(msg["Subject"])[0]
    if isinstance(asunto, bytes):
        asunto = asunto.decode(encoding if encoding else "utf-8")

    remitente = msg.get("From")
    fecha = msg.get("Date")

    # Extraer cuerpo
    cuerpo = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                cuerpo = part.get_payload(decode=True).decode(errors="ignore")
                break
    else:
        cuerpo = msg.get_payload(decode=True).decode(errors="ignore")

    categoria = clasificar_correo(asunto, remitente, cuerpo)

    print("\n📩 Asunto:", asunto)
    print("👤 De:", remitente)
    print("⏰ Fecha:", fecha)
    print("📝 Cuerpo:", cuerpo[:120], "...")
    print("📂 Categoría sugerida:", categoria)

imap.logout()
