import requests
from config import ACCESS_CODE, PHONE_ID
import json

def send_whatsapp_text(phone, message):
    url = f"https://graph.facebook.com/v19.0/{PHONE_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_CODE}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": message}
    }

    response = requests.post(url, headers=headers, json=payload, verify=False)

    print("🔍 WhatsApp API Response:", response.status_code, response.text)