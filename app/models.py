from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from sqlalchemy import Date
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
    products = relationship("Product", back_populates="client")
    rules = relationship("AutoReplyRule", back_populates="client")
    messages = relationship("MessageLog", back_populates="client")
    message_template = relationship("MessageTemplate", back_populates="client", uselist=False)
    token_valid = Column(Boolean, default=True)
    plan = Column(String, default="starter")
    payment_status = Column(String, default="unpaid")  # unpaid, paid, failed
    payment_reference = Column(String, nullable=True)
    waba_id = Column(String, nullable=True)
    subscription_start = Column(Date, nullable=True)
    subscription_end = Column(Date, nullable=True)
    subscription_months = Column(Integer, default=1)
    grace_period_end = Column(Date, nullable=True)
    reminder_7_sent = Column(Boolean, default=False)
    reminder_3_sent = Column(Boolean, default=False)
    ai_replies_used = Column(Integer, default=0)
    ai_replies_reset_date = Column(Date, nullable=True)
    business_description = Column(Text, nullable=True)
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

    id                  = Column(Integer, primary_key=True)
    client_id           = Column(Integer, ForeignKey("clients.id"))
    sender_number       = Column(String)
    message_text        = Column(Text)
    direction           = Column(String)
    timestamp           = Column(DateTime, default=datetime.utcnow)
    whatsapp_message_id = Column(String, nullable=True, unique=True)

    client = relationship("Client", back_populates="messages")
class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    opted_out = Column(Boolean, default=False)
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

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    image_public_id = Column(String, nullable=True)  # Cloudinary public ID for deletion
    category = Column(String, nullable=True)
    keyword = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="products")
class MessageTemplate(Base):
    __tablename__ = "message_templates"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    welcome_message = Column(Text, nullable=True)
    menu_message = Column(Text, nullable=True)
    closed_message = Column(Text, nullable=True)
    handoff_message = Column(Text, nullable=True)
    fallback_message = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    client = relationship("Client", back_populates="message_template")


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id           = Column(Integer, primary_key=True)
    name         = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
    price_kobo   = Column(Integer, nullable=False)
    description  = Column(String, nullable=True)
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    discount_3_months  = Column(Integer, default=10)   # 10% off
    discount_6_months  = Column(Integer, default=15)   # 15% off  
    discount_12_months = Column(Integer, default=20)   # 20% off
