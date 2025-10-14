import os
import re
import openai
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv

# Cargar variables de entorno desde sofia.env
load_dotenv("sofia.env")

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
IMAP_SERVER = "imap.gmail.com"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# --- Conexión IMAP a Gmail ---
try:
    print("DEBUG -> Conectando a Gmail IMAP...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_USER, EMAIL_PASS)
    print("✅ Conexión IMAP exitosa")
    
    # Seleccionar la bandeja de entrada
    mail.select("inbox")
    print("✅ Bandeja INBOX seleccionada")

    # Buscar correos no leídos
    status, mensajes = mail.search(None, 'UNSEEN')
    if status == "OK":
        correos_ids = mensajes[0].split()
        print(f"📩 Correos no leídos encontrados: {len(correos_ids)}")
    else:
        print("⚠️ No se pudo buscar correos.")

except Exception as e:
    print("❌ Error conectando a Gmail:")
    print(e)

# --- Reglas rápidas ---
RULES = {
    "Seguridad": [
        r"seguridad", r"alerta", r"contraseña", r"verificación",
        r"no-reply@accounts.google.com"
    ],
    "Finanzas": [
        r"factura", r"pago", r"recibo", r"transacción", r"banco"
    ],
    "Notificaciones": [
        r"linkedin", r"facebook", r"youtube", r"instagram", r"tiktok"
    ],
    "Promociones": [
        r"oferta", r"descuento", r"promoción", r"compra", r"rebaja"
    ]
}

def apply_rules(subject, sender, body):
    text = f"{subject} {sender} {body}".lower()
    for category, patterns in RULES.items():
        for pattern in patterns:
            if re.search(pattern, text):
                return category
    return None  # si no hay coincidencia

def classify_with_ai(subject, sender, body):
    prompt = f"""
    Clasifica este correo en una de las siguientes categorías:
    - Seguridad
    - Finanzas
    - Notificaciones
    - Promociones
    - Otros

    Asunto: {subject}
    Remitente: {sender}
    Cuerpo: {body[:200]}...

    Responde SOLO con el nombre de la categoría.
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ Error en clasificación IA:", e)
        return "Otros"

def process_email(subject, sender, body):
    # 1. Intentar con reglas rápidas
    category = apply_rules(subject, sender, body)

    # 2. Si no hay match, usar IA
    if not category:
        category = classify_with_ai(subject, sender, body)

    print(f"📂 Categoría final: {category}")
    return category

# --- Conexión IMAP y lectura ---
def read_inbox():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        status, messages = mail.search(None, "UNSEEN")
        email_ids = messages[0].split()

        for e_id in email_ids:
            status, msg_data = mail.fetch(e_id, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject, _ = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(errors="ignore")

            sender = msg.get("From")

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode()
                            break
                        except:
                            pass
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")

            print(f"\n📩 Asunto: {subject}")
            print(f"👤 De: {sender}")
            print(f"📝 Cuerpo: {body[:200]}...")

            category = process_email(subject, sender, body)

        mail.logout()
    except Exception as e:
        print("❌ Error leyendo bandeja:", e)

if __name__ == "__main__":
    print("DEBUG -> Archivo .env cargado")
    print(f"DEBUG -> EMAIL_USER: {EMAIL_USER}")
    print(f"DEBUG -> EMAIL_PASS: ****")
    read_inbox()
