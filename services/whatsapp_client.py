import os
import requests

# Estos los configurás como variables de entorno en Render o en tu .env local
WHATSAPP_TOKEN = "EAAaYkMbQ47IBP1eE6sLq62XpZCMWy6mHHNFdoWBxjdFDKTEAZBhq7k4IKkba2J7zQzEZBqOjqVPg16HP22PXZCc2c1mlZAvpZCeNzlNSEZCIltHabU8fZBEg2RHQX9lcqvEkUwS7YV9L2Th5UgVgm52Jw1ZBfeoKczfjplPfVdZBArRSZBHAqc4ETaIqCuyHNF3eAZDZD"
PHONE_NUMBER_ID = "886891177838505"


def send_text_message(to: str, text: str):
    """
    Envía un mensaje de texto simple por WhatsApp al número 'to'.
    """
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        print("⚠️ Falta configurar WHATSAPP_TOKEN o PHONE_NUMBER_ID")
        return

    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
    }

    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }

    try:
        resp = requests.post(url, headers=headers, json=data)
        print("📤 Enviando mensaje a WhatsApp...")
        print("Status:", resp.status_code)
        print("Respuesta:", resp.text)
    except Exception as e:
        print("❌ Error enviando mensaje a WhatsApp:", str(e))


def send_gif_message(to: str, gif_url: str):
    """
    Envía un GIF por WhatsApp usando URL pública.
    """
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        print("⚠️ Falta configurar WHATSAPP_TOKEN o PHONE_NUMBER_ID")
        return

    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
    }

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {"link": },
    }

    try:
        resp = requests.post(url, headers=headers, json=data)
        print("📤 Enviando GIF a WhatsApp...")
        print("Status:", resp.status_code)
        print("Respuesta:", resp.text)
    except Exception as e:
        print("❌ Error enviando GIF a WhatsApp:", str(e))
