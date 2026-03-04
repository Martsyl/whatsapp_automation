from fastapi import FastAPI
from app.database import engine, Base
from app import models
from app.routers import auth, admin, webhook, broadcast
from app.routers import payment
from apscheduler.schedulers.background import BackgroundScheduler
from app.subscription_checker import run_subscription_checks
Base.metadata.create_all(bind=engine)

app = FastAPI(title="WhatsApp Automation Admin")

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(webhook.router, prefix="/webhook", tags=["Webhook"])
app.include_router(broadcast.router, prefix="/broadcast", tags=["Broadcast"])
app.include_router(payment.router)


scheduler = BackgroundScheduler()
scheduler.add_job(
    run_subscription_checks,
    'cron',
    hour=8,        # Runs every day at 8am
    minute=0
)
scheduler.start()

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()
@app.get("/test-subscription-check/")
async def test_subscription_check():
    from app.subscription_checker import run_subscription_checks
    run_subscription_checks()
    return {"status": "check complete — see terminal for results"}
@app.get("/")
def root():
    return {"status": "running"}