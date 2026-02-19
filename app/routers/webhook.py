from fastapi import APIRouter, Request, Query
from app.database import SessionLocal
from app import models
from app.email import send_email_notification
import requests
import os
from datetime import datetime
import pytz

router = APIRouter()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")


def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        pass


def send_whatsapp_message(phone_number_id, access_token, recipient, message):
    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f"Send response: {response.status_code} - {response.json()}")


def is_new_user(db, client_id, sender):
    previous = db.query(models.MessageLog).filter(
        models.MessageLog.client_id == client_id,
        models.MessageLog.sender_number == sender,
        models.MessageLog.direction == "inbound"
    ).first()
    return previous is None


def auto_save_contact(db, client, sender):
    existing = db.query(models.Contact).filter(
        models.Contact.client_id == client.id,
        models.Contact.phone_number == sender
    ).first()

    if not existing:
        business_slug = client.business_name.lower().replace(" ", "_")
        contact_count = db.query(models.Contact).filter(
            models.Contact.client_id == client.id
        ).count()
        auto_name = f"{business_slug}_client_{contact_count + 1}"
        new_contact = models.Contact(
            client_id=client.id,
            name=auto_name,
            phone_number=sender
        )
        db.add(new_contact)
        db.commit()
        print(f"Auto-saved contact: {auto_name} - {sender}")


def is_within_business_hours(db, client_id):
    now = datetime.now(pytz.UTC)
    day = now.weekday()
    current_time = now.strftime("%H:%M")

    hours = db.query(models.BusinessHours).filter(
        models.BusinessHours.client_id == client_id,
        models.BusinessHours.day_of_week == day,
        models.BusinessHours.is_open == True
    ).first()

    if not hours:
        return True  # No hours set means always open

    return hours.open_time <= current_time <= hours.close_time


def get_greeting(business_name):
    return (
        f"👋 Welcome to *{business_name}*!\n\n"
        f"We're glad you reached out. Here's what we can help you with:\n\n"
        f"1️⃣ Type *price* - to see our pricing\n"
        f"2️⃣ Type *location* - to find us\n"
        f"3️⃣ Type *hours* - for our working hours\n"
        f"4️⃣ Type *human* - to speak with an agent\n\n"
        f"Just type any of the keywords above to get started! 😊"
    )


def get_menu():
    return (
        "📋 *Main Menu*\n\n"
        "1️⃣ Type *price* - Pricing info\n"
        "2️⃣ Type *location* - Find us\n"
        "3️⃣ Type *hours* - Working hours\n"
        "4️⃣ Type *human* - Talk to an agent\n\n"
        "Type *menu* anytime to see this again."
    )


def get_fallback():
    return (
        "🤔 Sorry, I didn't quite understand that.\n\n"
        "Type *menu* to see available options or *human* to speak with our team directly."
    )


@router.get("/")
def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    return {"error": "Verification failed"}


@router.post("/")
async def receive_message(request: Request):
    data = await request.json()
    db = get_db()

    try:
        value = data["entry"][0]["changes"][0]["value"]
        messages = value.get("messages", [])
        metadata = value.get("metadata", {})
        incoming_phone_number_id = metadata.get("phone_number_id")

        for message in messages:
            sender = message["from"]
            if message["type"] != "text":
                continue

            text = message["text"]["body"].lower().strip()
            print(f"Incoming from {sender}: {text}")

            # Find client
            client = db.query(models.Client).filter(
                models.Client.phone_number_id == incoming_phone_number_id,
                models.Client.is_active == True
            ).first()

            if not client:
                print("No client found for this phone number ID")
                continue

            # Auto-save contact
            auto_save_contact(db, client, sender)

            # Check business hours
            if not is_within_business_hours(db, client.id):
                reply = (
                    "🕐 *We're currently closed.*\n\n"
                    "Our team is not available right now but we'll get back to you "
                    "as soon as we open.\n\n"
                    "Type *hours* to see our working hours."
                )
                send_whatsapp_message(client.phone_number_id, client.access_token, sender, reply)
                db.add(models.MessageLog(
                    client_id=client.id,
                    sender_number=sender,
                    message_text=reply,
                    direction="outbound"
                ))
                db.commit()
                continue

            # Check if new user and send greeting
            if is_new_user(db, client.id, sender):
                reply = get_greeting(client.business_name)

                db.add(models.MessageLog(
                    client_id=client.id,
                    sender_number=sender,
                    message_text=text,
                    direction="inbound"
                ))
                db.commit()

                send_whatsapp_message(client.phone_number_id, client.access_token, sender, reply)

                db.add(models.MessageLog(
                    client_id=client.id,
                    sender_number=sender,
                    message_text=reply,
                    direction="outbound"
                ))
                db.commit()
                continue

            # Log inbound message
            db.add(models.MessageLog(
                client_id=client.id,
                sender_number=sender,
                message_text=text,
                direction="inbound"
            ))
            db.commit()

            # Handle menu keyword
            if text == "menu":
                reply = get_menu()

            # Handle human handoff
            elif "human" in text or "agent" in text:
                reply = (
                    "👤 *Connecting you to an agent...*\n\n"
                    "Please hold on, someone from our team will respond shortly.\n"
                    "Our working hours are Mon-Fri, 9am - 6pm."
                )
                # Send email notification
                send_email_notification(
                    client.email,
                    client.business_name,
                    sender,
                    text
                )

            else:
                reply = None
                rules = db.query(models.AutoReplyRule).filter(
                    models.AutoReplyRule.client_id == client.id,
                    models.AutoReplyRule.is_active == True
                ).all()

                for rule in rules:
                    if rule.trigger_keyword in text:
                        reply = rule.response_text
                        break

                if not reply:
                    reply = get_fallback()

            # Send reply
            send_whatsapp_message(client.phone_number_id, client.access_token, sender, reply)

            # Log outbound
            db.add(models.MessageLog(
                client_id=client.id,
                sender_number=sender,
                message_text=reply,
                direction="outbound"
            ))
            db.commit()

    except (KeyError, IndexError) as e:
        print(f"Webhook parse error: {e}")
    finally:
        db.close()

    return {"status": "ok"}