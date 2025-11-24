from fastapi import FastAPI, Request
from chat import bot
from services.whatsapp_client import send_text_message
import os

app = FastAPI()

VERIFY_TOKEN = "bot_delivery_YA_2025"


# =========================================================
# 1. ENDPOINT DE VERIFICACIÓN (Meta lo usa al configurar webhook)
# =========================================================

@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Este endpoint lo usa Meta para verificar que tu webhook es válido.
    """
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)

    return {"error": "Token inválido"}


# =========================================================
# 2. ENDPOINT PRINCIPAL PARA RECIBIR MENSAJES DE WHATSAPP
# =========================================================

@app.post("/webhook")
async def receive_message(request: Request):
    """
    Acá llegan TODOS los mensajes que escribe el usuario en WhatsApp.
    """
    payload = await request.json()

    try:
        # Extraer el ID del usuario y el texto del mensaje
        wa_id = extraer_wa_id(payload)
        mensaje = extraer_texto(payload)

        if not wa_id or not mensaje:
            return {"status": "ignored"}

        # Pasar mensaje al bot (chat.py)
        respuestas = bot.handle_message(wa_id, mensaje)

        # Enviar cada respuesta por WhatsApp
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
    Obtiene el número de WhatsApp del usuario que envió el mensaje.
    """
    try:
        return payload["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
    except Exception:
        return None


def extraer_texto(payload: dict) -> str | None:
    """
    Obtiene el texto del mensaje que envió el usuario.
    """
    try:
        return payload["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]
    except Exception:
        return None


