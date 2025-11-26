from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from services.whatsapp_client import send_text_message
from chat import bot
import os

app = FastAPI()

VERIFY_TOKEN = "bot_delivery_YA_2025"


@app.get("/whatsapp")
async def verify_webhook(
    hub_mode: str = "", hub_challenge: str = "", hub_verify_token: str = ""
):
    """
    Endpoint de verificación del webhook de Meta.
    Meta hace un GET a /whatsapp con estos parámetros.
    """
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        # Si el token coincide, devolvemos el challenge
        return PlainTextResponse(hub_challenge, status_code=200)
    return PlainTextResponse("Error de verificación", status_code=403)


@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Endpoint que recibe los mensajes de WhatsApp (POST desde Meta).
    """
    try:
        body = await request.json()

        entry = body.get("entry", [])
        if not entry:
            return {"status": "no_entry"}

        changes = entry[0].get("changes", [])
        if not changes:
            return {"status": "no_changes"}

        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        if not messages:
            # No hay mensajes (puede ser status, etc.)
            return {"status": "no_messages"}

        # 👇 ESTE ES EL MENSAJE QUE LLEGA DE WHATSAPP
        message = messages[0]
        wa_id = message.get("from")  # número de WhatsApp del usuario
        msg_id = message.get("id")  # ⚠️ ID ÚNICO DEL MENSAJE

        # --------- OBTENER SESIÓN Y FILTRAR DUPLICADOS ---------
        session = bot._get_session(wa_id)

        if session.last_message_id == msg_id:
            # Ya procesamos este mensaje antes, lo ignoramos
            print("🔁 Mensaje duplicado ignorado:", msg_id)
            return {"status": "duplicate_ignored"}

        # Guardamos el último id procesado
        session.last_message_id = msg_id

        # (opcional) Guardar el wa_id por si alguna vez lo necesitás en chat.py
        session.data["wa_id"] = wa_id
        # -------------------------------------------------------

        # Obtenemos el texto según el tipo
        msg_type = message.get("type")
        if msg_type == "text":
            text = message["text"]["body"]
        elif msg_type == "interactive":
            interactive = message.get("interactive", {})
            if "button_reply" in interactive:
                text = interactive["button_reply"]["title"]
            elif "list_reply" in interactive:
                text = interactive["list_reply"]["title"]
            else:
                text = ""
        else:
            text = ""

        if not text:
            send_text_message(
                wa_id,
                "Solo puedo procesar mensajes de texto por ahora 🙂",
            )
            return {"status": "no_text"}

        # Pasar el mensaje al bot (chat.py)
        respuestas = bot.handle_message(wa_id, text)

        # Enviar todas las respuestas como mensajes de texto
        for r in respuestas:
            send_text_message(wa_id, r)

        return {"status": "ok"}

    except Exception as e:
        print("Error procesando mensaje:", e)
        return {"status": "error", "detail": str(e)}
