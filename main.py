import os
import requests
from fastapi import FastAPI, Request, Query
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")  # you'll set this same string in Meta dashboard


def send_message(recipient, message):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"body": message}
    }
    requests.post(url, headers=headers, json=payload)


# Meta calls this to verify your webhook
@app.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    return {"error": "Verification failed"}


# Meta sends incoming messages here
@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    
    try:
        messages = data["entry"][0]["changes"][0]["value"]["messages"]
        for message in messages:
            sender = message["from"]
            if message["type"] == "text":
                text = message["text"]["body"].lower()
                print(f"Message from {sender}: {text}")
                
                # Simple auto-reply for now
                send_message(sender, f"Hello! You said: {text}")
    except (KeyError, IndexError):
        pass  # Ignore non-message events like status updates
    
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)