from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from chat import bot
from services.whatsapp_client import send_text_message
import os

app = FastAPI()
app.mount("/media", StaticFiles(directory="media"), name="media")


# =========================================================
# CONFIGURACIÓN
# =========================================================

# En Render deberías tener seteada la variable VERIFY_TOKEN con este valor.
# Si no está, usa "bot_delivery_YA_2025" por defecto.
VERIFY_TOKEN = "bot_delivery_YA_2025"


# =========================================================
# 1. ENDPOINT DE VERIFICACIÓN (Meta lo usa al configurar webhook)
#    -> Ojo: ahora es /whatsapp, no /webhook
# =========================================================


@app.get("/whatsapp")
async def verify_webhook(request: Request):
    """
    Endpoint que usa Meta para verificar el webhook.
    """
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        # Meta espera que devolvamos el challenge como número
        return int(challenge)

    return {"error": "Token inválido"}


# =========================================================
# 2. ENDPOINT PRINCIPAL PARA RECIBIR MENSAJES DE WHATSAPP
#    -> También en /whatsapp (POST)
# =========================================================


@app.post("/whatsapp")
async def receive_message(request: Request):
    """
    Acá llegan TODOS los mensajes que escriben al número de WhatsApp.
    """
    payload = await request.json()

    try:
        # Extraer el ID de WhatsApp y el texto del mensaje
        wa_id = extraer_wa_id(payload)
        mensaje = extraer_texto(payload)

        if not wa_id or not mensaje:
            # No vino mensaje de texto "normal"
            return {"status": "ignored"}

        # Pasar el mensaje al bot (chat.py)
        respuestas = bot.handle_message(wa_id, mensaje)

        # Enviar cada respuesta al usuario
        for respuesta in respuestas:
            send_text_message(wa_id, respuesta)

    except Exception as e:
        print("Error procesando mensaje:", e)

    return {"status": "ok"}


# =========================================================
# 3. FUNCIONES AUXILIARES PARA LEER EL PAYLOAD DE META
# =========================================================


def extraer_wa_id(payload: dict) -> str | None:
    """
    Devuelve el número de WhatsApp del remitente.
    """
    try:
        return payload["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
    except Exception:
        return None


def extraer_texto(payload: dict) -> str | None:
    """
    Devuelve el texto del mensaje enviado por el usuario.
    """
    try:
        return payload["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]
    except Exception:
        return None
