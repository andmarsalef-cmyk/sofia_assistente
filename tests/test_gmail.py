import os
import imaplib
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv("sofia.env")

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
IMAP_SERVER = os.getenv("IMAP_SERVER")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))

print("DEBUG -> Probando conexión IMAP...")
print("DEBUG -> Usuario:", EMAIL_USER)

try:
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_USER, EMAIL_PASS)
    print("✅ Conexión exitosa a Gmail")

    # Seleccionar bandeja INBOX
    mail.select("inbox")
    status, messages = mail.search(None, "UNSEEN")

    if status == "OK":
        correos = messages[0].split()
        print(f"📩 Correos no leídos encontrados: {len(correos)}")
    else:
        print("⚠️ No se pudo leer la bandeja")

    mail.logout()

except imaplib.IMAP4.error as e:
    print("❌ Error de autenticación:", e)
except Exception as e:
    print("❌ Otro error:", e)
