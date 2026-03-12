from fastapi import APIRouter

router = APIRouter(prefix="/payment", tags=["Payment"])

# Placeholder — Paystack callbacks are handled by Django
# This file exists so main.py can import it without errors