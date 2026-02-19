from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from app.database import get_db
from app import models
import os

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_client(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        client_id = int(payload.get("sub"))
        client = db.query(models.Client).filter(models.Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=401, detail="Client not found")
        return client
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# rest of routes stay the same...
@router.get("/me")
def get_profile(current_client=Depends(get_current_client)):
    return {
        "id": current_client.id,
        "business_name": current_client.business_name,
        "email": current_client.email,
        "whatsapp_number": current_client.whatsapp_number,
        "is_active": current_client.is_active
    }


@router.post("/rules")
def add_rule(
    trigger_keyword: str,
    response_text: str,
    db: Session = Depends(get_db),
    current_client=Depends(get_current_client)
):
    rule = models.AutoReplyRule(
        client_id=current_client.id,
        trigger_keyword=trigger_keyword.lower(),
        response_text=response_text
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return {"message": "Rule added successfully", "rule_id": rule.id}


@router.get("/rules")
def get_rules(db: Session = Depends(get_db), current_client=Depends(get_current_client)):
    rules = db.query(models.AutoReplyRule).filter(
        models.AutoReplyRule.client_id == current_client.id
    ).all()
    return rules


@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db), current_client=Depends(get_current_client)):
    rule = db.query(models.AutoReplyRule).filter(
        models.AutoReplyRule.id == rule_id,
        models.AutoReplyRule.client_id == current_client.id
    ).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
    return {"message": "Rule deleted"}


@router.get("/messages")
def get_messages(db: Session = Depends(get_db), current_client=Depends(get_current_client)):
    messages = db.query(models.MessageLog).filter(
        models.MessageLog.client_id == current_client.id
    ).order_by(models.MessageLog.timestamp.desc()).limit(50).all()
    return messages