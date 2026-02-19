from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    phone_number_id = Column(String, unique=True, nullable=False)
    whatsapp_number = Column(String, nullable=False)
    access_token = Column(String, nullable=False)
    contacts = relationship("Contact", back_populates="client")
    broadcasts = relationship("Broadcast", back_populates="client")
    business_hours = relationship("BusinessHours", back_populates="client")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    rules = relationship("AutoReplyRule", back_populates="client")
    messages = relationship("MessageLog", back_populates="client")


class AutoReplyRule(Base):
    __tablename__ = "auto_reply_rules"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    trigger_keyword = Column(String, nullable=False)  # e.g "price", "hello"
    response_text = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="rules")


class MessageLog(Base):
    __tablename__ = "message_logs"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    sender_number = Column(String, nullable=False)
    message_text = Column(Text, nullable=False)
    direction = Column(String, nullable=False)  # "inbound" or "outbound"
    timestamp = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="messages")
class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="contacts")


class Broadcast(Base):
    __tablename__ = "broadcasts"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    template_name = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, running, completed
    total = Column(Integer, default=0)
    sent = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="broadcasts")

class BusinessHours(Base):
    __tablename__ = "business_hours"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    open_time = Column(String, nullable=False)   # e.g "09:00"
    close_time = Column(String, nullable=False)  # e.g "18:00"
    is_open = Column(Boolean, default=True)

    client = relationship("Client", back_populates="business_hours")