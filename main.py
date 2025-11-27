from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from services.whatsapp_client import send_text_message
from services.whatsapp_client import send_text_message, send_interactive_list_message
from chat import bot
import asyncio

app = FastAPI()

VERIFY_TOKEN = "bot_delivery_YA_2025"


# ================== COLA DE MENSAJES 10s ==================


class MessageAggregator:
    """
    Maneja una cola de mensajes por usuario.
    Por cada mensaje:
      - se agrega al buffer de ese user_id
      - se resetea un timer de 10s
    Si pasan 10s sin mensajes nuevos:
      - se concatenan los textos
      - se llama al callback de procesamiento
    """

    def __init__(self):
        # user_id -> {"texts": [str, ...], "task": asyncio.Task}
        self._buffers: dict[str, dict] = {}

    async def add_message(self, user_id: str, text: str, process_callback):
        buf = self._buffers.get(user_id)

        if buf is None:
            buf = {"texts": [], "task": None}
            self._buffers[user_id] = buf

        buf["texts"].append(text)

        # Si ya había un timer corriendo, lo cancelamos
        task: asyncio.Task | None = buf.get("task")
        if task is not None and not task.done():
            task.cancel()

        # Lanzamos un nuevo timer de 10 segundos
        buf["task"] = asyncio.create_task(
            self._wait_and_process(user_id, process_callback)
        )

        async def _wait_and_process(self, user_id: str, process_callback):
        try:
            # Esperar 3 segundos desde el último mensaje
            await asyncio.sleep(3)

            buf = self._buffers.pop(user_id, None)
            if not buf:
                return

            texts = buf["texts"]
            if not texts:
                return

            # En lugar de concatenar todo en un solo string,
            # procesamos CADA mensaje por separado, en orden.
            for t in texts:
                t = t.strip()
                if not t:
                    continue
                await process_callback(user_id, t)

        except asyncio.CancelledError:
            # El timer se canceló porque llegó un nuevo mensaje
            return



message_aggregator = MessageAggregator()


async def process_user_message(user_id: str, text: str):
    """
    Esta función se ejecuta recién cuando pasan 3/10s sin mensajes nuevos.
    Aquí sí llamamos al bot y mandamos las respuestas.
    """
    respuestas = bot.handle_message(user_id, text)

    for r in respuestas:
        # Caso clásico: respuesta de texto
        if isinstance(r, str):
            # 👇 Evitar enviar mensajes vacíos o solo espacios
            if not r.strip():
                continue
            send_text_message(user_id, r)
            continue

        # Caso nuevo: respuesta interactiva tipo lista
        if isinstance(r, dict) and r.get("kind") == "interactive_list":
            sections = r.get("sections", [])
            send_interactive_list_message(
                to=user_id,
                header_text=r.get("header", "Menú"),
                body_text=r.get("body", "Elegí una opción de la lista"),
                footer_text=r.get("footer", ""),
                button_text=r.get("button", "Menu"),
                sections=sections,
            )
            continue


# ================== ENDPOINTS WHATSAPP ==================


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

        msg_type = message.get("type")
        text = ""

        if msg_type == "text":
            # Mensaje de texto normal
            text = message.get("text", {}).get("body", "")

        elif msg_type == "interactive":
            # Respuestas de botones/listas interactivas
            interactive = message.get("interactive", {})
            if "button_reply" in interactive:
                # Podés usar title o id; más adelante nos va a interesar el id
                text = interactive["button_reply"].get("id") or interactive[
                    "button_reply"
                ].get("title", "")
            elif "list_reply" in interactive:
                text = interactive["list_reply"].get("id") or interactive[
                    "list_reply"
                ].get("title", "")

        else:
            # Tipos no manejados (audio, imagen, etc.) por ahora
            text = ""

        if not text:
            # Si no hay texto entendible, no hacemos nada complejo
            send_text_message(
                wa_id,
                "Solo puedo procesar mensajes de texto o respuestas interactivas por ahora 🙂",
            )
            return {"status": "no_text"}

        # En vez de procesar de una, lo mandamos al agregador de 10 segundos
        await message_aggregator.add_message(wa_id, text, process_user_message)

        # Respondemos al webhook rápido; el procesamiento real se hará luego
        return {"status": "queued"}

    except Exception as e:
        print("Error procesando mensaje:", e)
        return {"status": "error", "detail": str(e)}
