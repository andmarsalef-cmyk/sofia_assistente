import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
import os

# Cargar variables
load_dotenv("sofia.env")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))

if not EMAIL_USER or not EMAIL_PASS:
    raise ValueError("❌ ERROR: Faltan EMAIL_USER o EMAIL_PASS en sofia.env")

print("DEBUG -> Archivo .env cargado")
print("DEBUG -> EMAIL_USER:", EMAIL_USER)
print("DEBUG -> EMAIL_PASS:", "****")

# Conexión IMAP con Gmail
mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
mail.login(EMAIL_USER, EMAIL_PASS)
mail.select("inbox")

# Buscar los últimos 5 correos
status, messages = mail.search(None, "ALL")
mail_ids = messages[0].split()
latest_ids = mail_ids[-5:]  # últimos 5 correos

for num in latest_ids:
    status, msg_data = mail.fetch(num, "(RFC822)")
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])

            # Asunto
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8", errors="ignore")

            # Remitente
            from_ = msg.get("From")

            # Fecha
            date_ = msg.get("Date")

            # Contenido (solo texto plano si lo hay)
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")

            snippet = body[:80].replace("\n", " ") + "..." if body else "(sin contenido)"

            print(f"\n📩 Asunto: {subject}")
            print(f"👤 De: {from_}")
            print(f"⏰ Fecha: {date_}")
            print(f"📝 Contenido: {snippet}")

mail.logout()

