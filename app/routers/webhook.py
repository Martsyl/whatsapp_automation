from fastapi import APIRouter, Request, Query, BackgroundTasks
from app.database import SessionLocal
from app import models
from app.email import send_email_notification
import requests
import os
import re
import time
from datetime import datetime, date
import pytz

router = APIRouter()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")


# ─────────────────────────────────────────────
# WHATSAPP HELPERS
# ─────────────────────────────────────────────

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
    result = response.json()
    print(f"Send response: {response.status_code} - {result}")

    if "error" in result:
        error_code = result["error"].get("code")
        if error_code in [190, 102, 10]:
            print(f"TOKEN ERROR detected for phone_number_id {phone_number_id}")
            flag_client_token_error(phone_number_id)

    return response


def send_whatsapp_image(phone_number_id, access_token, recipient, image_url, caption):
    if 'cloudinary.com' in image_url:
        image_url = re.sub(r'\.(avif|webp|png|gif)$', '.jpg', image_url)
        print(f"Converted image URL to: {image_url}")

    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "image",
        "image": {
            "link": image_url,
            "caption": caption
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    result = response.json()
    print(f"Image send response: {response.status_code} - {result}")
    if "error" in result:
        print(f"IMAGE SEND ERROR: {result['error']}")
    return response


def flag_client_token_error(phone_number_id):
    db = SessionLocal()
    try:
        client = db.query(models.Client).filter(
            models.Client.phone_number_id == phone_number_id
        ).first()
        if client:
            client.token_valid = False
            db.commit()
            print(f"Flagged token error for client: {client.business_name}")
    except Exception as e:
        print(f"Error flagging token: {e}")
    finally:
        db.close()


# ─────────────────────────────────────────────
# CONTACT & USER HELPERS
# ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# BUSINESS HOURS
# ─────────────────────────────────────────────

def is_within_business_hours(db, client_id):
    nigeria_tz   = pytz.timezone("Africa/Lagos")
    now          = datetime.now(nigeria_tz)
    day          = now.weekday()
    current_time = now.strftime("%H:%M")

    print(f"Current Nigeria time: {current_time}, Day: {day}")

    hours = db.query(models.BusinessHours).filter(
        models.BusinessHours.client_id == client_id,
        models.BusinessHours.day_of_week == day,
        models.BusinessHours.is_open == True
    ).first()

    if not hours:
        return True

    if not hours.open_time or not hours.close_time:
        return True

    print(f"Business hours: {hours.open_time} - {hours.close_time}")

    if hours.close_time < hours.open_time:
        return current_time >= hours.open_time or current_time <= hours.close_time
    else:
        return hours.open_time <= current_time <= hours.close_time


# ─────────────────────────────────────────────
# MESSAGE BUILDERS
# ─────────────────────────────────────────────

def get_greeting(business_name, products=None, rules=None):
    categories = {}
    if products:
        for product in products:
            cat = product.category or "Products"
            if cat not in categories:
                categories[cat] = cat

    menu_items = ""
    item_num   = 1

    if categories:
        for cat in categories.values():
            menu_items += f"{item_num}️⃣ Type *{cat.lower()}* - Browse {cat}\n"
            item_num += 1

    if rules:
        for rule in rules:
            menu_items += f"{item_num}️⃣ Type *{rule.trigger_keyword}* - {rule.response_text[:30]}\n"
            item_num += 1

    menu_items += f"{item_num}️⃣ Type *menu* - See all options\n"
    item_num   += 1
    menu_items += f"{item_num}️⃣ Type *human* - Talk to an agent\n"

    return (
        f"👋 Welcome to *{business_name}*!\n\n"
        f"We're glad you reached out. Here's what we offer:\n\n"
        f"{menu_items}\n"
        f"Just type any keyword above to get started! 😊"
    )


def get_menu(business_name, products=None, rules=None):
    categories = {}
    if products:
        for product in products:
            cat = product.category or "Products"
            if cat not in categories:
                categories[cat] = cat

    menu_items = ""
    item_num   = 1

    if categories:
        for cat in categories.values():
            menu_items += f"{item_num}️⃣ Type *{cat.lower()}* - Browse {cat}\n"
            item_num += 1

    if rules:
        for rule in rules:
            menu_items += f"{item_num}️⃣ Type *{rule.trigger_keyword}* - Info\n"
            item_num += 1

    menu_items += f"{item_num}️⃣ Type *human* - Talk to an agent\n"

    return (
        f"📋 *{business_name} Menu*\n\n"
        f"{menu_items}\n"
        f"Type *menu* anytime to see this again."
    )


def get_fallback():
    return (
        "🤔 Sorry, I didn't quite understand that.\n\n"
        "Type *menu* to see available options or *human* to speak with our team directly."
    )


def get_client_templates(db, client):
    return db.query(models.MessageTemplate).filter(
        models.MessageTemplate.client_id == client.id
    ).first()


def build_welcome(template, business_name, active_products, active_rules):
    if template and template.welcome_message:
        return template.welcome_message.replace("{business_name}", business_name)
    return get_greeting(business_name, active_products, active_rules)


def build_menu(template, business_name, active_products, active_rules):
    if template and template.menu_message:
        return template.menu_message.replace("{business_name}", business_name)
    return get_menu(business_name, active_products, active_rules)


def build_closed(template):
    if template and template.closed_message:
        return template.closed_message
    return (
        "🕐 *We're currently closed.*\n\n"
        "Our team is not available right now but we'll get back to you "
        "as soon as we open.\n\n"
        "Type *hours* to see our working hours."
    )


def build_handoff(template):
    if template and template.handoff_message:
        return template.handoff_message
    return (
        "👤 *Connecting you to an agent...*\n\n"
        "Please hold on, someone from our team will respond shortly.\n"
        "Our working hours are Mon-Fri, 9am - 6pm."
    )


def build_fallback(template):
    if template and template.fallback_message:
        return template.fallback_message
    return get_fallback()


# ─────────────────────────────────────────────
# AI REPLY WITH RETRY
# ─────────────────────────────────────────────

def get_ai_reply_with_retry(client, text, db):
    """Call AI reply with one retry on overload (529)"""
    try:
        from app.ai_reply import get_ai_reply
    except ImportError:
        return None

    for attempt in range(2):
        try:
            ai_response = get_ai_reply(client, text, db)
            return ai_response
        except Exception as e:
            error_str = str(e)
            if '529' in error_str or 'overloaded' in error_str.lower():
                if attempt == 0:
                    print(f"⚠️ Claude overloaded, retrying in 2s...")
                    time.sleep(2)
                    continue
                else:
                    print(f"❌ Claude still overloaded after retry — using fallback")
                    return None
            else:
                print(f"❌ AI reply error: {e}")
                return None

    return None


# ─────────────────────────────────────────────
# DEDUPLICATION CHECK
# ─────────────────────────────────────────────

def is_duplicate_message(db, whatsapp_message_id):
    """Check if this exact message was already processed"""
    if not whatsapp_message_id:
        return False
    existing = db.query(models.MessageLog).filter(
        models.MessageLog.whatsapp_message_id == whatsapp_message_id
    ).first()
    return existing is not None


# ─────────────────────────────────────────────
# CORE MESSAGE PROCESSOR (runs in background)
# ─────────────────────────────────────────────

def process_message(data: dict):
    db = SessionLocal()

    try:
        value                    = data["entry"][0]["changes"][0]["value"]
        messages_list            = value.get("messages", [])
        metadata                 = value.get("metadata", {})
        incoming_phone_number_id = metadata.get("phone_number_id")

        for message in messages_list:
            sender = message["from"]
            if message["type"] != "text":
                continue

            text               = message["text"]["body"].lower().strip()
            whatsapp_message_id = message.get("id")

            print(f"Incoming from {sender}: {text}")

            # ── Deduplication — skip if already processed ──
            if is_duplicate_message(db, whatsapp_message_id):
                print(f"⚠️ Duplicate webhook ignored: {whatsapp_message_id}")
                continue

            # ── Find client ──
            client = db.query(models.Client).filter(
                models.Client.phone_number_id == incoming_phone_number_id,
                models.Client.is_active == True
            ).first()

            if not client:
                print("No client found for this phone number ID")
                continue

            # ── Check subscription ──
            today = date.today()
            if client.grace_period_end and today > client.grace_period_end:
                print(f"❌ Subscription expired for {client.business_name} — bot paused")
                continue

            # ── Auto-save contact ──
            auto_save_contact(db, client, sender)

            # ── Handle opt-out ──
            if text == "stop":
                contact = db.query(models.Contact).filter(
                    models.Contact.client_id == client.id,
                    models.Contact.phone_number == sender
                ).first()
                if contact:
                    contact.opted_out = True
                    db.commit()

                reply = (
                    "✅ You have been unsubscribed successfully.\n\n"
                    "You will no longer receive messages from us.\n"
                    "Type *START* anytime to resubscribe."
                )
                send_whatsapp_message(client.phone_number_id, client.access_token, sender, reply)
                db.add(models.MessageLog(
                    client_id=client.id,
                    sender_number=sender,
                    message_text=reply,
                    direction="outbound",
                    whatsapp_message_id=whatsapp_message_id
                ))
                db.commit()
                continue

            # ── Handle opt-in ──
            if text == "start":
                contact = db.query(models.Contact).filter(
                    models.Contact.client_id == client.id,
                    models.Contact.phone_number == sender
                ).first()
                if contact:
                    contact.opted_out = False
                    db.commit()

                reply = (
                    "✅ You have been resubscribed successfully.\n\n"
                    "You will now receive messages from us again.\n"
                    "Type *STOP* anytime to unsubscribe."
                )
                send_whatsapp_message(client.phone_number_id, client.access_token, sender, reply)
                db.add(models.MessageLog(
                    client_id=client.id,
                    sender_number=sender,
                    message_text=reply,
                    direction="outbound",
                    whatsapp_message_id=whatsapp_message_id
                ))
                db.commit()
                continue

            # ── Block opted-out contacts ──
            contact = db.query(models.Contact).filter(
                models.Contact.client_id == client.id,
                models.Contact.phone_number == sender
            ).first()

            if contact and contact.opted_out:
                print(f"Skipping opted-out contact: {sender}")
                continue

            # ── Fetch active products, rules, templates ──
            active_products = db.query(models.Product).filter(
                models.Product.client_id == client.id,
                models.Product.is_active == True
            ).all()

            active_rules = db.query(models.AutoReplyRule).filter(
                models.AutoReplyRule.client_id == client.id,
                models.AutoReplyRule.is_active == True
            ).all()

            template = get_client_templates(db, client)

            # ── Check business hours ──
            if not is_within_business_hours(db, client.id):
                reply = build_closed(template)
                send_whatsapp_message(client.phone_number_id, client.access_token, sender, reply)
                db.add(models.MessageLog(
                    client_id=client.id,
                    sender_number=sender,
                    message_text=reply,
                    direction="outbound",
                    whatsapp_message_id=whatsapp_message_id
                ))
                db.commit()
                continue

            # ── New user — send welcome ──
            if is_new_user(db, client.id, sender):
                reply = build_welcome(template, client.business_name, active_products, active_rules)

                db.add(models.MessageLog(
                    client_id=client.id,
                    sender_number=sender,
                    message_text=text,
                    direction="inbound",
                    whatsapp_message_id=whatsapp_message_id
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

            # ── Log inbound message ──
            db.add(models.MessageLog(
                client_id=client.id,
                sender_number=sender,
                message_text=text,
                direction="inbound",
                whatsapp_message_id=whatsapp_message_id
            ))
            db.commit()

            # ── Menu ──
            if text == "menu":
                reply = build_menu(template, client.business_name, active_products, active_rules)
                send_whatsapp_message(client.phone_number_id, client.access_token, sender, reply)
                db.add(models.MessageLog(
                    client_id=client.id,
                    sender_number=sender,
                    message_text=reply,
                    direction="outbound"
                ))
                db.commit()
                continue

            # ── Human handoff ──
            elif "human" in text or "agent" in text:
                reply = build_handoff(template)
                send_email_notification(client.email, client.business_name, sender, text)
                send_whatsapp_message(client.phone_number_id, client.access_token, sender, reply)
                db.add(models.MessageLog(
                    client_id=client.id,
                    sender_number=sender,
                    message_text=reply,
                    direction="outbound"
                ))
                db.commit()
                continue

            else:
                reply = None

                # ── 1. Auto-reply rules ──
                for rule in active_rules:
                    if rule.trigger_keyword in text:
                        reply = rule.response_text
                        break

                # ── 2. Category match ──
                if not reply:
                    matching_category_products = db.query(models.Product).filter(
                        models.Product.client_id == client.id,
                        models.Product.is_active == True,
                        models.Product.category.ilike(text)
                    ).all()

                    if matching_category_products:
                        category_name = matching_category_products[0].category
                        product_list  = f"🛍️ *{category_name}*\n\n"
                        product_list += "Here are our available products:\n\n"
                        for p in matching_category_products:
                            product_list += (
                                f"▪️ *{p.name}*\n"
                                f"   💰 {p.price}\n"
                                f"   Type *{p.keyword}* for details\n\n"
                            )
                        product_list += "Type the keyword next to any product to see full details!"
                        reply = product_list

                # ── 3. Individual product keyword ──
                if not reply:
                    product = db.query(models.Product).filter(
                        models.Product.client_id == client.id,
                        models.Product.keyword == text,
                        models.Product.is_active == True
                    ).first()

                    if product:
                        if product.image_url:
                            send_whatsapp_image(
                                client.phone_number_id,
                                client.access_token,
                                sender,
                                product.image_url,
                                f"*{product.name}*\n\n"
                                f"{product.description}\n\n"
                                f"💰 {product.price}\n\n"
                                f"Type *order* to place an order or *menu* to see more options."
                            )
                            db.add(models.MessageLog(
                                client_id=client.id,
                                sender_number=sender,
                                message_text=f"[PRODUCT] {product.name}",
                                direction="outbound"
                            ))
                            db.commit()
                            continue
                        else:
                            reply = (
                                f"*{product.name}*\n\n"
                                f"{product.description}\n\n"
                                f"💰 {product.price}\n\n"
                                f"Type *order* to place an order or *menu* to see more options."
                            )

                # ── 4. AI reply (Growth & Pro) with retry ──
                if not reply:
                    reply = get_ai_reply_with_retry(client, text, db)
                    if reply:
                        print(f"🤖 AI reply sent to {sender}")

                # ── 5. Final fallback ──
                if not reply:
                    reply = build_fallback(template)

                # ── Send reply ──
                if reply:
                    send_whatsapp_message(
                        client.phone_number_id,
                        client.access_token,
                        sender,
                        reply
                    )
                    db.add(models.MessageLog(
                        client_id=client.id,
                        sender_number=sender,
                        message_text=reply,
                        direction="outbound"
                    ))
                    db.commit()

    except (KeyError, IndexError) as e:
        print(f"Webhook parse error: {e}")
    except Exception as e:
        print(f"Unexpected error in process_message: {e}")
    finally:
        db.close()


# ─────────────────────────────────────────────
# WEBHOOK ENDPOINTS
# ─────────────────────────────────────────────

@router.get("/")
def verify_webhook(
    hub_mode: str         = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str    = Query(None, alias="hub.challenge")
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    return {"error": "Verification failed"}


@router.post("/")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()

    # ── Return 200 to Meta IMMEDIATELY ──
    # Processing happens in background so Meta never retries
    background_tasks.add_task(process_message, data)

    return {"status": "ok"}