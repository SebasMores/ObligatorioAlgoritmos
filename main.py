from fastapi import FastAPI, Request, Query
from fastapi.responses import PlainTextResponse
from services.whatsapp_client import send_text_message
from chat import bot

app = FastAPI()

VERIFY_TOKEN = "bot_delivery_YA_2025"


# ---------- RUTA RAÍZ (para probar que el server está vivo) ----------
@app.get("/")
async def root():
    return {"status": "ok", "message": "WhatsApp bot funcionando"}


# ---------- GET /whatsapp (verificación del webhook) ----------
@app.get("/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """
    Meta llama a este endpoint con un GET para verificar el webhook.
    Usa los parámetros: hub.mode, hub.challenge, hub.verify_token
    """
    # Aceptamos sólo si el modo es "subscribe" y el token coincide
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        # devolvemos el challenge tal cual lo manda Meta
        return PlainTextResponse(hub_challenge or "", status_code=200)

    return PlainTextResponse("Error de verificación", status_code=403)


# ---------- POST /whatsapp (mensajes que llegan de WhatsApp) ----------
@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Endpoint que recibe los mensajes de WhatsApp (POST desde Meta).
    """
    try:
        body = await request.json()
        # print("BODY:", body)  # útil para debug

        entry = body.get("entry", [])
        if not entry:
            return {"status": "no_entry"}

        changes = entry[0].get("changes", [])
        if not changes:
            return {"status": "no_changes"}

        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        if not messages:
            # No hay mensajes (puede ser un evento de status, etc.)
            return {"status": "no_messages"}

        message = messages[0]
        wa_id = message.get("from")  # número de WhatsApp del usuario

        # Obtenemos el texto independientemente del tipo
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
            # Tipos no manejados (audio, imagen, etc.)
            text = ""

        if not text:
            send_text_message(
                wa_id, "Solo puedo procesar mensajes de texto por ahora 🙂"
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
