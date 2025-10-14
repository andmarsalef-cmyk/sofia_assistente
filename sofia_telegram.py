import os
import logging
import pickle
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from openai import OpenAI
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# === Configuración de logging ===
logging.basicConfig(
    filename="sofia.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# === Lista global para mapear números -> IDs de correos ===
correo_ids = []

# === Cargar claves desde sofia.env ===
load_dotenv("sofia.env")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# === Gmail API Config ===
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_gmail_service():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build("gmail", "v1", credentials=creds)

def find_attachments(payload):
    """Busca recursivamente todos los adjuntos en el payload de Gmail."""
    attachments = []

    def walk(part):
        fn = part.get("filename") or ""
        body = part.get("body", {}) or {}
        if fn and "attachmentId" in body:
            attachments.append((fn, body["attachmentId"]))
        for sub in part.get("parts", []) or []:
            walk(sub)

    walk(payload)
    return attachments

# === Handlers ===

# /start → bienvenida
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hola, soy Sofía. Te ayudo con tus correos.\nUsa /correos, /buscar <palabra>, /resumen."
    )

# === /correos: lista 5 no leídos, numerados y guarda sus IDs ===
async def listar_correos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global correo_ids
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

        correo_ids = []  # reiniciar IDs cada vez que listamos
        response_text = "📌 Últimos 5 correos no leídos:\n\n"

        for i, msg in enumerate(messages, start=1):
            correo_ids.append(msg["id"])   # guardar ID para usar con /leer
            msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
            payload = msg_data['payload']
            headers = payload.get('headers', [])

            remitente = next((h['value'] for h in headers if h['name'] == 'From'), "Desconocido")
            asunto = next((h['value'] for h in headers if h['name'] == 'Subject'), "Sin asunto")
            fecha = next((h['value'] for h in headers if h['name'] == 'Date'), "Sin fecha")

            response_text += f"{i}. {asunto} — {remitente} — {fecha}\n"

        await update.message.reply_text(response_text)

    except Exception as e:
        logger.exception("Error en /correos")
        await update.message.reply_text(f"⚠️ Error al listar correos: {e}")

# /buscar <palabra> → busca correos por palabra clave
async def buscar_correos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usa: /buscar <palabra>")
        return

    palabra = " ".join(context.args)
    try:
        service = get_gmail_service()
        results = service.users().messages().list(userId="me", q=palabra, maxResults=5).execute()
        messages = results.get("messages", [])

        if not messages:
            await update.message.reply_text(f"🔎 No encontré correos con '{palabra}'.")
            return

        response = f"🔎 Resultados con '{palabra}':\n"
        for msg in messages:
            m = service.users().messages().get(userId="me", id=msg["id"]).execute()
            payload = m['payload']
            headers = payload.get('headers', [])

            remitente = next((h['value'] for h in headers if h['name'] == 'From'), "Desconocido")
            asunto = next((h['value'] for h in headers if h['name'] == 'Subject'), "Sin asunto")
            fecha = next((h['value'] for h in headers if h['name'] == 'Date'), "Sin fecha")

            response += f"- {asunto} — {remitente} — {fecha}\n"

        await update.message.reply_text(response)

    except Exception as e:
        logger.exception("Error en /buscar")
        await update.message.reply_text(f"⚠️ Error al buscar correos: {e}")

# /resumen → resume últimos 5 correos no leídos
async def resumen_correos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global correo_ids
    try:
        service = get_gmail_service()
        results = service.users().messages().list(
            userId='me',
            labelIds=['INBOX', 'UNREAD'],
            maxResults=5
        ).execute()
        messages = results.get('messages', [])

        if not messages:
            await update.message.reply_text("📭 No tienes correos no leídos para resumir.")
            return

        response_text = "📌 Resúmenes de los últimos 5 correos no leídos:\n\n"
        correo_ids = []   # reiniciar IDs cada vez que listamos

        for i, msg in enumerate(messages, start=1):
            correo_ids.append(msg["id"])
            msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
            payload = msg_data['payload']
            headers = payload.get('headers', [])

            remitente = next((h['value'] for h in headers if h['name'] == 'From'), "Desconocido")
            asunto = next((h['value'] for h in headers if h['name'] == 'Subject'), "Sin asunto")
            fecha = next((h['value'] for h in headers if h['name'] == 'Date'), "Sin fecha")

            response_text += (
                f"📩 {i}. Asunto: {asunto}\n"
                f"De: {remitente}\n"
                f"Fecha: {fecha}\n"
                f"---\n"
            )

            # Adjuntos
            adjuntos = []
            for part in payload.get("parts", []):
                if part.get("filename"):
                    adjuntos.append(part["filename"])
            if adjuntos:
                response_text += f"📎 Adjuntos: {', '.join(adjuntos)}\n"

        await update.message.reply_text(response_text)

    except Exception as e:
        logger.exception("Error en /resumen")
        await update.message.reply_text(f"⚠️ Error al resumir correos: {e}")

# /leer <número> → abre un correo específico por su número en la lista
# === Función auxiliar para buscar adjuntos (recursiva) ===
def find_attachments(payload):
    """Busca recursivamente todos los adjuntos en el payload de Gmail."""
    attachments = []

    def walk(part):
        fn = part.get("filename") or ""
        body = part.get("body", {}) or {}
        if fn and "attachmentId" in body:
            attachments.append((fn, body["attachmentId"]))
        for sub in part.get("parts", []) or []:
            walk(sub)

    walk(payload)
    return attachments


# === /leer → Lee y resume el correo N ===
async def leer_correo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global correo_ids
    try:
        if not context.args:
            await update.message.reply_text("⚠️ Usa: /leer <número>")
            return

        num = int(context.args[0])
        if num < 1 or num > len(correo_ids):
            await update.message.reply_text("⚠️ Número fuera de rango. Primero ejecuta /correos para ver la lista.")
            return

        service = get_gmail_service()
        correo_id = correo_ids[num - 1]

        msg = service.users().messages().get(userId='me', id=correo_id, format='full').execute()
        payload = msg.get('payload', {})
        headers = payload.get('headers', [])

        remitente = next((h['value'] for h in headers if h['name'] == 'From'), "Desconocido")
        asunto = next((h['value'] for h in headers if h['name'] == 'Subject'), "Sin asunto")
        fecha = next((h['value'] for h in headers if h['name'] == 'Date'), "Sin fecha")

        # Obtener cuerpo del correo
        cuerpo = ""
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    import base64
                    cuerpo += base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
        elif "body" in payload and "data" in payload["body"]:
            import base64
            cuerpo += base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")

        # Resumir contenido con GPT
        resumen = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente que resume correos en español de forma clara y concisa."},
                {"role": "user", "content": f"Resume este correo en máximo 3 frases:\n{cuerpo}"}
            ]
        )
        resumen_texto = resumen.choices[0].message.content.strip()

        # Buscar adjuntos (robusto)
        attachments = find_attachments(payload)
        tiene_adjuntos = len(attachments) > 0

        # Armar respuesta
        response_text = f"📩 *Asunto:* {asunto}\n"
        response_text += f"👤 *De:* {remitente}\n"
        response_text += f"🕒 *Fecha:* {fecha}\n\n"
        response_text += f"📝 *Resumen:* {resumen_texto}\n"

        if tiene_adjuntos:
            response_text += "\n📎 *Adjuntos encontrados:*\n"
            for fn, _ in attachments:
                response_text += f"   • {fn}\n"

        await update.message.reply_text(response_text, parse_mode="Markdown")

    except Exception as e:
        logger.exception("Error al leer correo")
        await update.message.reply_text(f"⚠️ Error al leer el correo: {e}")
        await update.message.reply_text(f"⚠️ No se encontró adjunto con el nombre: {nombre_adjunto}")

    except Exception as e:
        logger.exception("Error en /adjunto")
        await update.message.reply_text(f"⚠️ Error al enviar adjunto: {e}")

# === /adjunto → envía un archivo adjunto del correo N ===
async def enviar_adjunto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global correo_ids
    if not context.args:
        await update.message.reply_text(
            "⚠️ Usa: /adjunto <número> [<nombre>|<índice>]\n"
            "Ejemplo: /adjunto 2 factura.pdf  ó  /adjunto 2 1"
        )
        return

    # Validar que el primer argumento sea número
    try:
        num = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "⚠️ El primer parámetro debe ser un número. Ejemplo: /adjunto 2 factura.pdf"
        )
        return

    if num < 1 or num > len(correo_ids):
        await update.message.reply_text(
            "⚠️ Número fuera de rango. Primero ejecuta /correos para ver la lista."
        )
        return

    try:
        service = get_gmail_service()
        correo_id = correo_ids[num - 1]
        msg = service.users().messages().get(userId='me', id=correo_id, format='full').execute()
        payload = msg.get('payload', {}) or {}

        # Buscar adjuntos (robusto)
        attachments = find_attachments(payload)
        if not attachments:
            await update.message.reply_text("ℹ️ Ese correo no tiene adjuntos.")
            return

        # Si solo pusieron el número, listar los adjuntos
        if len(context.args) == 1:
            lista = "\n".join(f"{i+1}. {fn}" for i, (fn, _) in enumerate(attachments))
            await update.message.reply_text(
                f"📎 Adjuntos disponibles en el correo {num}:\n{lista}\n\n"
                f"Para enviarlo: /adjunto {num} <nombre> o /adjunto {num} <índice>"
            )
            return

        criterio = " ".join(context.args[1:]).strip()
        elegido = None

        # Buscar por índice
        try:
            idx = int(criterio) - 1
            if 0 <= idx < len(attachments):
                elegido = attachments[idx]
        except ValueError:
            pass

        # Buscar por nombre (exacto o parcial)
        if elegido is None:
            crit_low = criterio.lower()
            for fn, aid in attachments:
                if crit_low in fn.lower():
                    elegido = (fn, aid)
                    break

        if elegido is None:
            lista = "\n".join(f"{i+1}. {fn}" for i, (fn, _) in enumerate(attachments))
            await update.message.reply_text(
                f"⚠️ No encontré un adjunto que coincida con '{criterio}'.\n\nAdjuntos disponibles:\n{lista}"
            )
            return

        # Descargar y enviar el adjunto
        fn, attach_id = elegido
        data = service.users().messages().attachments().get(
            userId='me', messageId=correo_id, id=attach_id
        ).execute()

        import base64
        from io import BytesIO
        file_bytes = base64.urlsafe_b64decode(data["data"])
        bio = BytesIO(file_bytes)
        bio.name = fn

        await update.message.reply_document(document=bio)

    except Exception as e:
        logger.exception("Error en /adjunto")
        await update.message.reply_text(f"⚠️ Error al enviar adjunto: {e}")

# === main ===
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("correos", listar_correos))
    app.add_handler(CommandHandler("buscar", buscar_correos))
    app.add_handler(CommandHandler("resumen", resumen_correos))
    app.add_handler(CommandHandler("leer", leer_correo))
    app.add_handler(CommandHandler("leer", leer_correo))
    app.add_handler(CommandHandler("adjunto", enviar_adjunto))
    print("🤖 Sofía está lista para ayudarte con tus correos...")
    app.run_polling()

if __name__ == "__main__":
    main()
