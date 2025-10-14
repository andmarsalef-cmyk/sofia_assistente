import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv("sofia.env")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

print("DEBUG -> Usuario:", EMAIL_USER)

try:
    # Conectar al servidor IMAP de Gmail
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL_USER, EMAIL_PASS)
    print("✅ Conectado a Gmail (IMAP)")

    # Seleccionar bandeja de entrada
    mail.select("inbox")

    # Buscar solo correos NO LEÍDOS
    status, mensajes = mail.search(None, "UNSEEN")
    mensajes = mensajes[0].split()

    if not mensajes:
        print("📭 No hay correos nuevos sin leer.")
    else:
        print(f"\n📩 Tienes {len(mensajes)} correos nuevos:\n")

        # Revisar los últimos 5 no leídos
        ultimos = mensajes[-5:]

        for num in reversed(ultimos):
            status, datos = mail.fetch(num, "(RFC822)")
            raw_email = datos[0][1]
            msg = email.message_from_bytes(raw_email)

            # Decodificar asunto
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else "utf-8")

            # Obtener remitente
            from_ = msg.get("From")

            print(f"De: {from_}")
            print(f"Asunto: {subject}")
            print("-" * 40)

    mail.logout()

except Exception as e:
    print("❌ Error al leer correos:")
    print(e)
