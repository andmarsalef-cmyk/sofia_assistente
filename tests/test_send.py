import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
import traceback

# Cargar variables del .env
load_dotenv("sofia.env")  # Asegúrate que el archivo se llame así
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

print("DEBUG -> Archivo .env cargado")
print("DEBUG -> EMAIL_USER:", EMAIL_USER)
print("DEBUG -> EMAIL_PASS:", EMAIL_PASS[:4] + "****" if EMAIL_PASS else "No cargada")

# Configuración del correo
destinatario = EMAIL_USER  # Te envías un correo a ti mismo para probar
msg = MIMEMultipart()
msg["From"] = EMAIL_USER
msg["To"] = destinatario
msg["Subject"] = "Prueba desde Sofía"

cuerpo = "¡Hola! Este es un correo de prueba enviado desde Sofía 🚀"
msg.attach(MIMEText(cuerpo, "plain"))

try:
    # Servidor SMTP para Gmail
    with smtplib.SMTP("smtp.gmail.com", 587) as s:
        s.ehlo()
        s.starttls()
        s.login(EMAIL_USER, EMAIL_PASS)
        s.send_message(msg)
    print("✅ Correo de prueba enviado correctamente. Revisa tu bandeja de entrada.")
except Exception as e:
    print("❌ Error al enviar el correo de prueba:")
    traceback.print_exc()
    
     
