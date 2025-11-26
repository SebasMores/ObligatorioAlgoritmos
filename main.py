from fastapi import FastAPI, Request, Query
from fastapi.responses import PlainTextResponse
from services.whatsapp_client import send_text_message
from chat import bot


app = FastAPI()

VERIFY_TOKEN = "bot_delivery_YA_2025"


@app.get("/")
async def root():
    return {"status": "ok", "message": "WhatsApp bot funcionando"}


@app.get("/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    # Solo para ver en logs que llega de Meta
    print("GET /whatsapp verify:", hub_mode, hub_verify_token, hub_challenge)

    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        # Meta espera que devolvamos EXACTAMENTE el challenge
        return PlainTextResponse(hub_challenge or "", status_code=200)

    return PlainTextResponse("Error de verificación", status_code=403)


@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    try:
        body = await request.json()
        print("POST /whatsapp BODY:", body)

        entry = body.get("entry", [])
        if not entry:
            return {"status": "no_entry"}

        changes = entry[0].get("changes", [])
        if not changes:
            return {"status": "no_changes"}

        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return {"status": "no_messages"}

        message = messages[0]
        wa_id = message.get("from")

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
                wa_id, "Solo puedo procesar mensajes de texto por ahora 🙂"
            )
            return {"status": "no_text"}

        respuestas = bot.handle_message(wa_id, text)
        for r in respuestas:
            send_text_message(wa_id, r)

        return {"status": "ok"}

    except Exception as e:
        print("Error procesando mensaje:", e)
        return {"status": "error", "detail": str(e)}
