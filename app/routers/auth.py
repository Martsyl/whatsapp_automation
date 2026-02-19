from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from app.database import get_db
from app import models
import os

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Admin registers a new client
@router.post("/register")
def register_client(
    business_name: str,
    email: str,
    password: str,
    phone_number_id: str,
    whatsapp_number: str,
    access_token: str,
    db: Session = Depends(get_db)
):
    existing = db.query(models.Client).filter(models.Client.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    client = models.Client(
        business_name=business_name,
        email=email,
        hashed_password=hash_password(password),
        phone_number_id=phone_number_id,
        whatsapp_number=whatsapp_number,
        access_token=access_token
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return {"message": f"Client '{business_name}' registered successfully", "client_id": client.id}


# Client logs in and gets a JWT token
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    client = db.query(models.Client).filter(models.Client.email == form_data.username).first()
    if not client or not verify_password(form_data.password, client.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(client.id), "email": client.email})
    return {"access_token": token, "token_type": "bearer"}