# ==========================================
# Sofia Telegram Bot - Versión limpia Render
# ==========================================
import os
import base64
import logging
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ========= Cargar entorno =========
from dotenv import load_dotenv
import os
import logging
from openai import OpenAI

# Cargar variables desde sofia.env (local) o entorno Render
load_dotenv("sofia.env")

# Variables críticas
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GMAIL_TOKEN_JSON = os.getenv("GMAIL_TOKEN_JSON")

# Validaciones claras (fallar rápido)
if not TELEGRAM_TOKEN:
    raise RuntimeError("❌ TELEGRAM_TOKEN no está definido")

if not OPENAI_API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY no está definido")

# Cliente OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Logging
logging.basicConfig(
    filename="sofia.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Marca de arranque (visible en logs)
print("=== SOFIA ENV CARGADO OK ===", flush=True)
print("TELEGRAM_TOKEN existe?:", bool(TELEGRAM_TOKEN), flush=True)
print("GMAIL_TOKEN_JSON existe?:", bool(GMAIL_TOKEN_JSON), flush=True)

# ======================================================
# 🔥 GMAIL SERVICE (100% Render-safe, SIN navegador)
# ======================================================
def get_gmail_service():
    """
    Gmail service SIN navegador.
    Lee GMAIL_TOKEN_JSON (JSON en una sola línea) y refresca con refresh_token.
    """
    import json
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

    token_json = os.getenv("GMAIL_TOKEN_JSON")
    if not token_json:
        raise RuntimeError("Falta la variable de entorno GMAIL_TOKEN_JSON")

    # Parsear JSON
    try:
        d = json.loads(token_json)
    except Exception as e:
        raise RuntimeError(f"GMAIL_TOKEN_JSON no es JSON válido: {e}")

    # Construir credenciales (sin usar archivos, sin OAuth interactivo)
    creds = Credentials(
        token=d.get("token"),
        refresh_token=d.get("refresh_token"),
        token_uri=d.get("token_uri"),
        client_id=d.get("client_id"),
        client_secret=d.get("client_secret"),
        scopes=SCOPES,
    )

    # Refrescar si está expirado (SIN navegador)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    # Validación final
    if not creds.valid:
        raise RuntimeError(
            "Token Gmail inválido o sin refresh_token (no se puede refrescar sin navegador)."
        )

    return build("gmail", "v1", credentials=creds, cache_discovery=False)
# ======================================================
# /correos – listar no leídos
# ======================================================
correo_ids = []

async def listar_correos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global correo_ids

    await update.message.reply_text("📥 Cargando correos, dame unos segundos...")

    try:
        service = get_gmail_service()

        res = service.users().messages().list(
            userId="me",
            labelIds=["INBOX"],
            q="is:unread",
            maxResults=5
        ).execute()

        messages = res.get("messages", [])
        if not messages:
            await update.message.reply_text("📭 No tienes correos no leídos.")
            return

        correo_ids = []
        lineas = ["📌 Últimos 5 correos no leídos:\n"]

        for i, msg in enumerate(messages, start=1):
            msg_id = msg["id"]
            correo_ids.append(msg_id)

            msg_data = service.users().messages().get(
                userId="me",
                id=msg_id,
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"]
            ).execute()

            headers_list = msg_data.get("payload", {}).get("headers", [])
            headers = {h.get("name"): h.get("value") for h in headers_list}

            remitente = headers.get("From", "Desconocido")
            asunto = headers.get("Subject", "Sin asunto")
            fecha = headers.get("Date", "Sin fecha")

            lineas.append(f"📩 {i}. {asunto}\nDe: {remitente}\nFecha: {fecha}\n")

        await update.message.reply_text("".join(lineas))

    except Exception as e:
        import traceback
        print("=== TRACEBACK /correos ===")
        print(traceback.format_exc())
        print("=== FIN TRACEBACK ===")
        logger.exception("Error en /correos")
        await update.message.reply_text(f"⚠️ Error al listar correos: {e}")

# ======================================================
# /resumen – Resumir últimos 5 correos
# ======================================================
async def resumen_correos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        service = get_gmail_service()
        res = service.users().messages().list(
            userId="me",
            labelIds=["INBOX"],
            q="is:unread",
            maxResults=5
        ).execute()

        mensajes = res.get("messages", [])
        if not mensajes:
            await update.message.reply_text("📭 No tienes correos no leídos.")
            return

        texto_final = "📌 *Resúmenes de los últimos 5 correos:* \n\n"
        import base64

        for i, msg in enumerate(mensajes, start=1):
            msg_data = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="full"
            ).execute()

            payload = msg_data.get("payload", {})
            headers = payload.get("headers", [])

            remitente = next((h["value"] for h in headers if h["name"] == "From"), "Desconocido")
            asunto = next((h["value"] for h in headers if h["name"] == "Subject"), "Sin asunto")

            cuerpo = ""
            if "parts" in payload:
                for part in payload["parts"]:
                    if part.get("mimeType") == "text/plain":
                        data = part.get("body", {}).get("data")
                        if data:
                            cuerpo = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                            break

            if not cuerpo:
                cuerpo = "(Sin texto legible)"

            # === RESUMEN CON IA ===
            resumen = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Resume este correo en un párrafo corto."},
                    {"role": "user", "content": cuerpo}
                ],
                max_tokens=120
            ).choices[0].message.content.strip()

            texto_final += f"📩 *{i}. {asunto}*\n"
            texto_final += f"👤 {remitente}\n"
            texto_final += f"🧠 {resumen}\n\n"

        await update.message.reply_text(texto_final, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error al crear el resumen: {e}")

# ======================================================
# /leer <n> – mostrar contenido
# ======================================================
async def leer_correo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global correo_ids
    try:
        if not context.args:
            await update.message.reply_text("⚠️ Usa: /leer <número>")
            return

        n = int(context.args[0])
        if n < 1 or n > len(correo_ids):
            await update.message.reply_text("⚠️ Número fuera de rango. Ejecuta /correos primero.")
            return
        await update.message.reply_text("📥 Cargando correo, por favor espera...")
        service = get_gmail_service()
        msg_id = correo_ids[n - 1]

        msg = service.users().messages().get(
            userId="me", id=msg_id, format="full"
        ).execute()

        payload = msg["payload"]
        headers = payload.get("headers", [])

        remitente = next((h["value"] for h in headers if h["name"] == "From"), "Desconocido")
        asunto = next((h["value"] for h in headers if h["name"] == "Subject"), "Sin asunto")
        fecha = next((h["value"] for h in headers if h["name"] == "Date"), "Sin fecha")

        # Extraer cuerpo ----------------------------------------------------
        def obtener_texto(partes):
            for part in partes:
                data = part.get("body", {}).get("data")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

                if "parts" in part:
                    t = obtener_texto(part["parts"])
                    if t:
                        return t
            return None

        cuerpo = ""
        if "parts" in payload:
            cuerpo = obtener_texto(payload["parts"]) or ""
        elif "data" in payload.get("body", {}):
            cuerpo = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")

        if not cuerpo:
            cuerpo = "(No contiene texto legible)"

        mensaje = (
            f"Asunto: {asunto}\n"
            f"De: {remitente}\n"
            f"Fecha: {fecha}\n\n"
            f"{cuerpo}"
        )

        for i in range(0, len(mensaje), 4000):
            await update.message.reply_text(
                mensaje[i:i+4000],
                parse_mode=None
            )

    except Exception as e:
        logger.exception("Error en /leer")
        await update.message.reply_text(f"⚠️ Error al leer correo: {e}")


# ======================================================
# /buscar <palabra>
# ======================================================
async def buscar_correos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global correo_ids

    try:
        if not context.args:
            await update.message.reply_text("⚠️ Usa: /buscar <palabra>")
            return

        palabra = " ".join(context.args)
        service = get_gmail_service()

        res = service.users().messages().list(
            userId="me",
            q=palabra,
            maxResults=5
        ).execute()

        messages = res.get("messages", [])
        if not messages:
            await update.message.reply_text("📭 No se encontraron correos.")
            return

        correo_ids = []
        texto = f"🔍 Resultados para '{palabra}':\n\n"

        for i, msg in enumerate(messages, start=1):
            correo_ids.append(msg["id"])
            full = service.users().messages().get(userId="me", id=msg["id"]).execute()
            headers = full["payload"].get("headers", [])

            remitente = next((h["value"] for h in headers if h["name"] == "From"), "Desconocido")
            asunto = next((h["value"] for h in headers if h["name"] == "Subject"), "Sin asunto")
            fecha = next((h["value"] for h in headers if h["name"] == "Date"), "Sin fecha")

            texto += f"📩 {i}. {asunto} — {remitente} — {fecha}\n"

        await update.message.reply_text(texto)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error en /buscar: {e}")


# ======================================================
# /hora
# ======================================================
async def hora_actual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await update.message.reply_text(f"🕒 Hora actual: {ahora}")


# ======================================================
# /texto normal → ChatGPT
# ======================================================
async def responder_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        respuesta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres Sofía, una asistente amable y clara."},
                {"role": "user", "content": update.message.text}
            ]
        )
        await update.message.reply_text(respuesta.choices[0].message.content)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hola, soy Sofía.\nUsa /correos para ver tus correos."
    )
# === DEBUG seguro (NO imprime el token) ===
_g = os.getenv("GMAIL_TOKEN_JSON")
print("DEBUG Render → GMAIL_TOKEN_JSON existe?:", bool(_g))
print("DEBUG Render → Longitud GMAIL_TOKEN_JSON:", len(_g) if _g else 0)
print("=== BOOT SOFIA ===")
print("TELEGRAM_TOKEN existe?:", bool(os.getenv("TELEGRAM_TOKEN")))
print("GMAIL_TOKEN_JSON existe?:", bool(os.getenv("GMAIL_TOKEN_JSON")))
t = os.getenv("GMAIL_TOKEN_JSON") or ""
print("GMAIL_TOKEN_JSON longitud:", len(t))
print("=== FIN BOOT ===")
# ======================================================
# MAIN
# ======================================================
def main():
    print("🤖 Sofía iniciando…")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("correos", listar_correos))
    app.add_handler(CommandHandler("buscar", buscar_correos))
    app.add_handler(CommandHandler("leer", leer_correo))
    app.add_handler(CommandHandler("resumen", resumen_correos))
    app.add_handler(CommandHandler("hora", hora_actual))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_texto))

    print("🤖 Sofía LISTA (Render OK)")
    app.run_polling()


if __name__ == "__main__":
    main()

