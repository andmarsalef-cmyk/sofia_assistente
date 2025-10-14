import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
import os

# Cargar variables del .env
load_dotenv("sofia.env")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

print("DEBUG -> Archivo .env cargado")
print("DEBUG -> EMAIL_USER:", EMAIL_USER)
print("DEBUG -> EMAIL_PASS:", "****" if EMAIL_PASS else "No cargada")

try:
    # Conexión al servidor IMAP de Gmail
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")

    # Buscar los 5 correos más recientes
    status, messages = mail.search(None, "ALL")
    if status == "OK":
        ids = messages[0].split()
        ultimos = ids[-5:]

        for num in ultimos:
            status, msg_data = mail.fetch(num, "(RFC822)")
            if status != "OK":
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8")
            print("📩 Asunto:", subject)
    else:
        print("❌ No se pudo acceder a la bandeja de entrada")

    mail.logout()
except Exception as e:
    print("❌ Error al leer correos:")
    print(e)
