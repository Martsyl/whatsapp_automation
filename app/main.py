from fastapi import FastAPI
from app.database import engine, Base
from app import models
from app.routers import auth, admin, webhook, broadcast

Base.metadata.create_all(bind=engine)

app = FastAPI(title="WhatsApp Automation Admin")

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(webhook.router, prefix="/webhook", tags=["Webhook"])
app.include_router(broadcast.router, prefix="/broadcast", tags=["Broadcast"])

@app.get("/")
def root():
    return {"status": "running"}