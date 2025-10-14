# ==============================
# 📧 Utilidades para manejo de correos
# ==============================
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
import os

# 🔹 Cargar variables de entorno
load_dotenv("sofia.env")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

def get_correos(n=5):
    """
    Lee los últimos 'n' correos de la bandeja de entrada de Gmail.
    Retorna un string con un resumen de cada correo.
    """
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL_USER, EMAIL_PASS)
        imap.select("inbox")

        status, messages = imap.search(None, "ALL")
        if status != "OK":
            return "⚠️ No se pudieron obtener correos."

        email_ids = messages[0].split()[-n:]
        resumen = []

        for num in email_ids:
            _, msg_data = imap.fetch(num, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Asunto
            asunto, encoding = decode_header(msg["Subject"])[0]
            if isinstance(asunto, bytes):
                asunto = asunto.decode(encoding if encoding else "utf-8", errors="ignore")

            remitente = msg.get("From")
            fecha = msg.get("Date")

            # Resumen corto del cuerpo
            cuerpo = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        cuerpo = part.get_payload(decode=True).decode(errors="ignore")
                        break
            else:
                cuerpo = msg.get_payload(decode=True).decode(errors="ignore")

            cuerpo_resumen = (cuerpo[:100] + "...") if len(cuerpo) > 100 else cuerpo

            resumen.append(f"📩 {asunto}\n👤 {remitente}\n⏰ {fecha}\n📝 {cuerpo_resumen}\n")

        imap.logout()
        return "\n".join(resumen) if resumen else "📭 No hay correos recientes."

    except Exception as e:
        return f"⚠️ Error al leer correos: {e}"
