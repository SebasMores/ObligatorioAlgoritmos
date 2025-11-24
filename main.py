from fastapi import FastAPI, HTTPException, Request
from utils.get_message_type import get_message_type
from chat import bot
import os

app = FastAPI()

# =========================
# CONFIGURACIÓN
# =========================

VERIFY_TOKEN = "bot_delivery_YA_2025"


@app.get("/welcome")
def index():
    return {"mensaje": "welcome developer"}


# =========================
# VERIFICACIÓN DE WEBHOOK
# =========================

@app.get("/whatsapp")
async def verify_token(request: Request):
    try:
        query_params = request.query_params

        verify_token = query_params.get("hub.verify_token")
        challenge = query_params.get("hub.challenge")

        if verify_token and challenge and verify_token == VERIFY_TOKEN:
            return int(challenge)
        else:
            raise HTTPException(status_code=400, detail="Token de verificación inválido")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en la verificación: {e}")


# =========================
# RECEPCIÓN DE MENSAJES
# =========================

@app.post("/whatsapp")
async def received_message(request: Request):
    try:
        body = await request.json()

        entry = body.get("entry", [])
        if not entry:
            return "EVENT_RECEIVED"

        changes = entry[0].get("changes", [])
        if not changes:
            return "EVENT_RECEIVED"

        value = changes[0].get("value", {})

        if "messages" not in value:
            return "EVENT_RECEIVED"

        messages = value["messages"]
        if not messages:
            return "EVENT_RECEIVED"

        message = messages[0]

        type_message, content = get_message_type(message)
        number = message.get("from")

        print("=====================================")
        print(f"📩 Mensaje recibido")
        print(f"De: {number}")
        print(f"Tipo: {type_message}")
        print(f"Contenido: {content}")
        print("=====================================")

        # 👉 Aquí enganchamos el Chat
        if type_message == "text":
            bot.user_phone = number
            bot.process_message(content)

        return "EVENT_RECEIVED"

    except Exception as e:
        print("❌ Error procesando mensaje:", str(e))
        return "EVENT_RECEIVED"


# =========================
# EJECUCIÓN LOCAL
# =========================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

