from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.routers.admin import get_current_client
import requests

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        pass


def send_whatsapp_template(phone_number_id, access_token, recipient, template_name):
    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "en_US"}
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f"Broadcast send to {recipient}: {response.status_code}")
    return response.status_code == 200


def run_broadcast(broadcast_id: int):
    # Create its own DB session for background task
    db = SessionLocal()
    try:
        broadcast = db.query(models.Broadcast).filter(models.Broadcast.id == broadcast_id).first()
        if not broadcast:
            return

        client = db.query(models.Client).filter(models.Client.id == broadcast.client_id).first()
        contacts = db.query(models.Contact).filter(models.Contact.client_id == broadcast.client_id).all()

        broadcast.status = "running"
        broadcast.total = len(contacts)
        db.commit()

        for contact in contacts:
            success = send_whatsapp_template(
                client.phone_number_id,
                client.access_token,
                contact.phone_number,
                broadcast.template_name
            )

            if success:
                broadcast.sent += 1
                db.add(models.MessageLog(
                    client_id=client.id,
                    sender_number=contact.phone_number,
                    message_text=f"[BROADCAST] {broadcast.title}",
                    direction="outbound"
                ))
            else:
                broadcast.failed += 1

            db.commit()

        broadcast.status = "completed"
        db.commit()
        print(f"Broadcast {broadcast_id} completed. Sent: {broadcast.sent}, Failed: {broadcast.failed}")

    except Exception as e:
        print(f"Broadcast error: {e}")
    finally:
        db.close()


# Add a contact
@router.post("/contacts")
def add_contact(
    name: str,
    phone_number: str,
    db: Session = Depends(get_db),
    current_client=Depends(get_current_client)
):
    existing = db.query(models.Contact).filter(
        models.Contact.client_id == current_client.id,
        models.Contact.phone_number == phone_number
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Contact already exists")

    contact = models.Contact(
        client_id=current_client.id,
        name=name,
        phone_number=phone_number
    )
    db.add(contact)
    db.commit()
    return {"message": "Contact added", "id": contact.id}


# Get all contacts
@router.get("/contacts")
def get_contacts(db: Session = Depends(get_db), current_client=Depends(get_current_client)):
    return db.query(models.Contact).filter(
        models.Contact.client_id == current_client.id
    ).all()


# Delete a contact
@router.delete("/contacts/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db), current_client=Depends(get_current_client)):
    contact = db.query(models.Contact).filter(
        models.Contact.id == contact_id,
        models.Contact.client_id == current_client.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(contact)
    db.commit()
    return {"message": "Contact deleted"}


# Create and launch broadcast
@router.post("/broadcast")
def create_broadcast(
    title: str,
    template_name: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_client=Depends(get_current_client)
):
    contacts_count = db.query(models.Contact).filter(
        models.Contact.client_id == current_client.id
    ).count()

    if contacts_count == 0:
        raise HTTPException(status_code=400, detail="No contacts to send to")

    broadcast = models.Broadcast(
        client_id=current_client.id,
        title=title,
        message=title,
        template_name=template_name,
        status="pending"
    )
    db.add(broadcast)
    db.commit()
    db.refresh(broadcast)

    # Run in background
    background_tasks.add_task(run_broadcast, broadcast.id)

    return {
        "message": f"Broadcast started for {contacts_count} contacts",
        "broadcast_id": broadcast.id
    }


# Get broadcast history
@router.get("/broadcasts")
def get_broadcasts(db: Session = Depends(get_db), current_client=Depends(get_current_client)):
    return db.query(models.Broadcast).filter(
        models.Broadcast.client_id == current_client.id
    ).order_by(models.Broadcast.created_at.desc()).all()


# Check broadcast status
@router.get("/broadcasts/{broadcast_id}")
def get_broadcast_status(broadcast_id: int, db: Session = Depends(get_db), current_client=Depends(get_current_client)):
    broadcast = db.query(models.Broadcast).filter(
        models.Broadcast.id == broadcast_id,
        models.Broadcast.client_id == current_client.id
    ).first()
    if not broadcast:
        raise HTTPException(status_code=404, detail="Broadcast not found")
    return broadcast