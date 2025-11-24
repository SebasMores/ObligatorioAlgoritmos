import os
import requests

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")      # tu token de acceso de Meta
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")    # el ID tipo 5009... que te dio Meta


def send_text_message(to: str, text: str):
    """
    Envía un mensaje de texto simple por WhatsApp al número 'to'.
    """
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        print("⚠️ Falta configurar WHATSAPP_TOKEN o PHONE_NUMBER_ID en variables de entorno")
        return

    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
    }

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": text
        },
    }

    try:
        resp = requests.post(url, headers=headers, json=data)
        print("📤 Enviando mensaje a WhatsApp...")
        print("Status:", resp.status_code)
        print("Respuesta:", resp.text)
    except Exception as e:
        print("❌ Error enviando mensaje a WhatsApp:", str(e))