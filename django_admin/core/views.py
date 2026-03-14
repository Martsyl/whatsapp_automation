# ── Standard library ──
import io
import os
import re
import json
import hmac
import secrets
import hashlib
import logging

# ── Django ──
from django.http import JsonResponse, HttpResponse, FileResponse, Http404
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.core.paginator import Paginator
from django.core.cache import cache
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

# ── Third party ──
import requests as http_requests
from passlib.context import CryptContext
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.graphics.barcode import code128

# ── Internal ──
from datetime import date, datetime, timedelta
from .models import (
    Client, AutoReplyRule, MessageLog, Contact,
    Broadcast, BusinessHours, Product, MessageTemplate,
    PasswordResetToken, SubscriptionPlan, PaymentLog, ErrorLog,
)
from .cloudinary_helper import upload_image, delete_image
from .email_helper import (
    send_password_reset_email,
    send_new_client_notification,
    send_renewal_notification,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─────────────────────────────────────────────
# LOGIN RATE LIMITING
# Tracks failed attempts in the DB cache.
# After 5 failures: 15-minute lockout per email.
# ─────────────────────────────────────────────
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 15 * 60  # 15 minutes


def _login_cache_keys(email):
    safe = email.replace('@', '_').replace('.', '_')
    return f'login_attempts_{safe}', f'login_lockout_{safe}'


def _is_locked_out(email):
    _, lockout_key = _login_cache_keys(email)
    return cache.get(lockout_key) is not None


def _record_failed_attempt(email):
    attempts_key, lockout_key = _login_cache_keys(email)
    attempts = cache.get(attempts_key, 0) + 1
    cache.set(attempts_key, attempts, timeout=LOGIN_LOCKOUT_SECONDS)
    if attempts >= LOGIN_MAX_ATTEMPTS:
        cache.set(lockout_key, True, timeout=LOGIN_LOCKOUT_SECONDS)
    return attempts


def _clear_login_attempts(email):
    attempts_key, lockout_key = _login_cache_keys(email)
    cache.delete(attempts_key)
    cache.delete(lockout_key)

# Hardcoded fallback prices (used only if DB is empty)
PLAN_PRICES = {
    "starter": 800000,
    "growth":  1800000,
    "pro":     3500000
}

PLAN_LIMITS = {
    "starter": {
        "max_rules":    10,
        "max_products": 10,
        "max_contacts": 500,
        "ai_replies":   0,
        "broadcast":    False,
    },
    "growth": {
        "max_rules":    float('inf'),
        "max_products": float('inf'),
        "max_contacts": float('inf'),
        "ai_replies":   100,
        "broadcast":    True,
    },
    "pro": {
        "max_rules":    float('inf'),
        "max_products": float('inf'),
        "max_contacts": float('inf'),
        "ai_replies":   float('inf'),
        "broadcast":    True,
    },
}


def get_plan_limits(plan):
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["starter"])


def get_plans_from_db():
    """Fetch active plans from DB as a dict keyed by name. Falls back gracefully."""
    try:
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price_naira')
        return {p.name: p for p in plans}
    except Exception as e:
        print(f"Could not fetch plans from DB: {e}")
        return {}


# ─────────────────────────────────────────────
# AUTH HELPERS
# ─────────────────────────────────────────────

def client_required(view_func):
    def wrapper(request, *args, **kwargs):
        if 'client_id' not in request.session:
            return redirect('client_login')

        # Allow renew and payment pages through without subscription check
        exempt_views = ['renew', 'payment_verify', 'renew_verify', 'client_logout', 'pending']
        if request.resolver_match and request.resolver_match.url_name in exempt_views:
            return view_func(request, *args, **kwargs)

        try:
            client = Client.objects.get(id=request.session['client_id'])
        except Client.DoesNotExist:
            request.session.flush()
            return redirect('client_login')

        today = date.today()

        # ── No subscription at all (just registered, haven't paid) ──
        if client.payment_status == 'unpaid' or not client.subscription_end:
            return redirect('subscribe')

        # ── Grace period check ──
        if client.grace_period_end and today > client.grace_period_end:
            messages.error(
                request,
                '⚠️ Your subscription has expired. Please renew to continue.'
            )
            return redirect('renew')

        # ── Subscription expired (but still in grace period — allow in, show warning) ──
        # The warning banner is shown via days_left in the template context

        return view_func(request, *args, **kwargs)
    return wrapper
def client_login(request):
    if request.method == 'POST':
        email    = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '').strip()

        # ── Rate limit check ──
        if _is_locked_out(email):
            messages.error(
                request,
                '⚠️ Too many failed attempts. Your account has been temporarily locked. '
                'Please try again in 15 minutes.'
            )
            return render(request, 'core/login.html', {'email': email})

        try:
            client = Client.objects.get(email=email)

            if not pwd_context.verify(password, client.hashed_password):
                attempts = _record_failed_attempt(email)
                remaining = LOGIN_MAX_ATTEMPTS - attempts
                if remaining > 0:
                    messages.error(
                        request,
                        f'Invalid email or password. '
                        f'{remaining} attempt{"s" if remaining != 1 else ""} remaining before lockout.'
                    )
                else:
                    messages.error(
                        request,
                        '⚠️ Too many failed attempts. '
                        'Your account has been locked for 15 minutes.'
                    )
                return render(request, 'core/login.html', {'email': email})

            # ── Account not activated by admin yet ──
            if not client.is_active:
                messages.error(
                    request,
                    '⏳ Your account is pending activation. '
                    "You'll receive an email once approved."
                )
                return render(request, 'core/login.html', {'email': email})

            # ── Successful login — clear any recorded failures ──
            _clear_login_attempts(email)
            request.session['client_id']   = client.id
            request.session['client_name'] = client.business_name

            today = date.today()

            if client.payment_status == 'unpaid' or not client.subscription_end:
                return redirect('subscribe')

            if client.grace_period_end and today > client.grace_period_end:
                messages.warning(
                    request,
                    '⚠️ Your subscription has expired. Please renew to access your dashboard.'
                )
                return redirect('renew')

            if client.subscription_end and today > client.subscription_end:
                messages.warning(
                    request,
                    f'⚠️ Your subscription expired on '
                    f'{client.subscription_end.strftime("%d %b %Y")}. '
                    f'Please renew soon to avoid interruption.'
                )
                return redirect('renew')

            return redirect('dashboard')

        except Client.DoesNotExist:
            # Record attempt for non-existent emails too
            # prevents user enumeration via timing difference
            _record_failed_attempt(email)
            messages.error(request, 'Invalid email or password.')

    return render(request, 'core/login.html')

def client_logout(request):
    request.session.flush()
    return redirect('landing')


# ─────────────────────────────────────────────
# LANDING & REGISTRATION
# ─────────────────────────────────────────────

def landing(request):
    client_id = request.session.get('client_id')
    if client_id:
        try:
            client = Client.objects.get(id=client_id, is_active=True)
            return redirect('dashboard')
        except Client.DoesNotExist:
            request.session.flush()

    plans_dict = get_plans_from_db()

    return render(request, 'core/index.html', {
        'starter': plans_dict.get('starter'),
        'growth':  plans_dict.get('growth'),
        'pro':     plans_dict.get('pro'),
    })


def register(request):
    if request.method == 'POST':
        business_name   = request.POST.get('business_name', '').strip()
        email           = request.POST.get('email', '').strip().lower()
        password        = request.POST.get('password', '').strip()
        confirm         = request.POST.get('confirm_password', '').strip()
        whatsapp_number = request.POST.get('whatsapp_number', '').strip()

        if not all([business_name, email, password, confirm, whatsapp_number]):
            return render(request, 'core/register.html', {
                'error': 'All fields are required.',
                'business_name': business_name,
                'email': email,
                'whatsapp_number': whatsapp_number,
            })

        if password != confirm:
            return render(request, 'core/register.html', {
                'error': 'Passwords do not match.',
                'business_name': business_name,
                'email': email,
                'whatsapp_number': whatsapp_number,
            })

        if len(password) < 6:
            return render(request, 'core/register.html', {
                'error': 'Password must be at least 6 characters.',
                'business_name': business_name,
                'email': email,
                'whatsapp_number': whatsapp_number,
            })

        if Client.objects.filter(email=email).exists():
            return render(request, 'core/register.html', {
                'error': 'An account with this email already exists.',
                'business_name': business_name,
                'whatsapp_number': whatsapp_number,
            })

        client = Client.objects.create(
            business_name=business_name,
            email=email,
            hashed_password=pwd_context.hash(password),
            whatsapp_number=whatsapp_number,
            is_active=False,
            payment_status='unpaid'
        )

        request.session['pending_client_id'] = client.id
        return redirect('meta_setup')

    return render(request, 'core/register.html')


def meta_setup(request):
    client_id = request.session.get('pending_client_id')
    if not client_id:
        return redirect('register')

    client = Client.objects.get(id=client_id)

    if request.method == 'POST':
        access_token    = request.POST.get('access_token', '').strip()
        phone_number_id = request.POST.get('phone_number_id', '').strip()
        waba_id         = request.POST.get('waba_id', '').strip()

        if not all([access_token, phone_number_id, waba_id]):
            return render(request, 'core/meta_setup.html', {
                'error': 'All fields are required.',
                'client': client,
                'access_token': access_token,
                'phone_number_id': phone_number_id,
                'waba_id': waba_id,
            })

        try:
            url      = f"https://graph.facebook.com/v19.0/{phone_number_id}"
            headers  = {"Authorization": f"Bearer {access_token}"}
            response = http_requests.get(url, headers=headers, timeout=10)
            result   = response.json()

            if "error" in result:
                error_code = result["error"].get("code", "")
                error_msg  = result["error"].get("message", "Invalid token")

                if error_code == 190:
                    friendly = "Your access token is invalid or has expired. Please generate a new one."
                elif error_code == 100:
                    friendly = "Phone Number ID is incorrect. Please check and try again."
                elif error_code == 10:
                    friendly = "Your token doesn't have the required WhatsApp permissions."
                else:
                    friendly = f"Meta verification failed: {error_msg}"

                return render(request, 'core/meta_setup.html', {
                    'error': friendly,
                    'client': client,
                    'access_token': access_token,
                    'phone_number_id': phone_number_id,
                    'waba_id': waba_id,
                })

        except Exception:
            return render(request, 'core/meta_setup.html', {
                'error': 'Could not reach Meta API. Please check your internet connection.',
                'client': client,
                'access_token': access_token,
                'phone_number_id': phone_number_id,
                'waba_id': waba_id,
            })

        # ── Check if phone_number_id already belongs to another account ──
        existing = Client.objects.filter(
            phone_number_id=phone_number_id
        ).exclude(id=client.id).first()

        if existing:
            return render(request, 'core/meta_setup.html', {
                'error': (
                    'This WhatsApp Phone Number ID is already registered to another account. '
                    'Each WhatsApp number can only be connected to one BotMart account. '
                    'If this is your number, please contact support.'
                ),
                'client': client,
                'access_token': access_token,
                'phone_number_id': phone_number_id,
                'waba_id': waba_id,
            })

        client.access_token    = access_token
        client.phone_number_id = phone_number_id
        client.waba_id         = waba_id
        client.token_valid     = True
        client.save()

        return redirect('subscribe')

    return render(request, 'core/meta_setup.html', {'client': client})


def subscribe(request):
    client_id = request.session.get('pending_client_id')
    if not client_id:
        return redirect('register')

    client     = Client.objects.get(id=client_id)
    error      = request.GET.get('error')
    plans_dict = get_plans_from_db()

    if request.method == 'POST':
        plan     = request.POST.get('plan', 'starter')
        months   = int(request.POST.get('months', 1))
        plan_obj = plans_dict.get(plan)
        base_amount = plan_obj.price_kobo if plan_obj else PLAN_PRICES.get(plan, 800000)

        # ── Calculate discounted amount based on duration ──
        if months == 3:
            discount_pct = getattr(plan_obj, 'discount_3_months', 10) if plan_obj else 10
        elif months == 6:
            discount_pct = getattr(plan_obj, 'discount_6_months', 15) if plan_obj else 15
        elif months == 12:
            discount_pct = getattr(plan_obj, 'discount_12_months', 20) if plan_obj else 20
        else:
            discount_pct = 0

        total_amount = int(base_amount * months * (1 - discount_pct / 100))

        try:
            response = http_requests.post(
                "https://api.paystack.co/transaction/initialize",
                headers={
                    "Authorization": f"Bearer {os.getenv('PAYSTACK_SECRET_KEY')}",
                    "Content-Type": "application/json"
                },
                json={
                    "email":        client.email,
                    "amount":       total_amount,
                    "currency":     "NGN",
                    "callback_url": f"{os.getenv('BASE_URL')}/payment/verify/",
                    "metadata": {
                        "client_id": client.id,
                        "plan":      plan,
                        "months":    months,
                        "email":     client.email
                    },
                    "channels": ["card", "bank", "ussd", "bank_transfer", "mobile_money"]
                }
            )
            data = response.json()

            if data["status"]:
                return redirect(data["data"]["authorization_url"])
            else:
                return render(request, 'core/subscribe.html', {
                    'client':  client,
                    'error':   'Payment initialization failed. Please try again.',
                    'starter': plans_dict.get('starter'),
                    'growth':  plans_dict.get('growth'),
                    'pro':     plans_dict.get('pro'),
                })

        except Exception as e:
            return render(request, 'core/subscribe.html', {
                'client':  client,
                'error':   f'Something went wrong: {str(e)}',
                'starter': plans_dict.get('starter'),
                'growth':  plans_dict.get('growth'),
                'pro':     plans_dict.get('pro'),
            })

    return render(request, 'core/subscribe.html', {
        'client':  client,
        'error':   error,
        'starter': plans_dict.get('starter'),
        'growth':  plans_dict.get('growth'),
        'pro':     plans_dict.get('pro'),
    })

# ─────────────────────────────────────────────
# PAYMENT VERIFY
# ─────────────────────────────────────────────

def payment_verify(request):
    reference = request.GET.get('reference')
    if not reference:
        return redirect('subscribe')

    try:
        response = http_requests.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers={
                "Authorization": f"Bearer {os.getenv('PAYSTACK_SECRET_KEY')}",
            }
        )
        data = response.json()

        if not data["status"] or data["data"]["status"] != "success":
            return redirect('/subscribe/?error=Payment+verification+failed')

        metadata  = data["data"]["metadata"]
        client_id = metadata.get("client_id")
        plan      = metadata.get("plan", "starter")
        months    = int(metadata.get("months", 1))

        client = Client.objects.get(id=client_id)

        # ── Calculate subscription dates ──
        today = date.today()
        days  = months * 30 if months < 12 else 365

        client.plan               = plan
        client.payment_status     = "paid"
        client.payment_reference  = reference
        client.subscription_start = today
        client.subscription_end   = today + timedelta(days=days)
        client.grace_period_end   = today + timedelta(days=days + 7)
        client.subscription_months = months
        client.reminder_7_sent    = False
        client.reminder_3_sent    = False
        client.save()
        PaymentLog.objects.create(
            client            = client,
            reference         = reference,
            amount_kobo       = data["data"]["amount"],
            plan              = plan,
            months            = months,
            is_renewal        = metadata.get("is_renewal", False),
            subscription_start = client.subscription_start,
            subscription_end  = client.subscription_end,
        )
            # Clear pending session
        request.session.pop('pending_client_id', None)

        return redirect('pending')

    except Exception as e:
        print(f"Payment verify error: {e}")
        return redirect('/subscribe/?error=Something+went+wrong')


# ─────────────────────────────────────────────
# RENEWAL VERIFY
# ─────────────────────────────────────────────

def renew_verify(request):
    reference = request.GET.get('reference')
    if not reference:
        return redirect('renew')

    try:
        response = http_requests.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers={
                "Authorization": f"Bearer {os.getenv('PAYSTACK_SECRET_KEY')}",
            }
        )
        data = response.json()

        if not data["status"] or data["data"]["status"] != "success":
            messages.error(request, 'Payment verification failed. Please contact support.')
            return redirect('renew')

        metadata  = data["data"]["metadata"]
        client_id = metadata.get("client_id")
        plan      = metadata.get("plan", "starter")
        months    = int(metadata.get("months", 1))

        # ── Fix: convert string "true"/"false" to boolean ──
        is_renewal = str(metadata.get("is_renewal", "false")).lower() == "true"

        client = Client.objects.get(id=client_id)

        # ── Skip if already processed by webhook ──
        if PaymentLog.objects.filter(reference=reference).exists():
            messages.success(
                request,
                f'✅ Subscription renewed for {months} month{"s" if months > 1 else ""}! '
                f'Active until {client.subscription_end.strftime("%d %b %Y")}.'
            )
            return redirect('dashboard')

        # ── Extend from current end date or today (whichever is later) ──
        today = date.today()
        days  = months * 30 if months < 12 else 365
        base  = max(client.subscription_end, today) if client.subscription_end else today

        client.plan                = plan
        client.payment_status      = "paid"
        client.payment_reference   = reference
        client.subscription_start  = today
        client.subscription_end    = base + timedelta(days=days)
        client.grace_period_end    = base + timedelta(days=days + 7)
        client.subscription_months = months
        client.reminder_7_sent     = False
        client.reminder_3_sent     = False
        client.is_active           = True
        client.save()

        PaymentLog.objects.create(
            client             = client,
            reference          = reference,
            amount_kobo        = data["data"]["amount"],
            plan               = plan,
            months             = months,
            is_renewal         = is_renewal,
            subscription_start = client.subscription_start,
            subscription_end   = client.subscription_end,
        )

        messages.success(
            request,
            f'✅ Subscription renewed for {months} month{"s" if months > 1 else ""}! '
            f'Active until {client.subscription_end.strftime("%d %b %Y")}.'
        )
        return redirect('dashboard')

    except Exception as e:
        print(f"Renew verify error: {e}")
        messages.error(request, 'Something went wrong. Please contact support.')
        return redirect('renew')
    
def pending(request):
    client_id = request.session.get('pending_client_id')
    client    = None
    if client_id:
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            pass
    return render(request, 'core/pending.html', {'client': client})


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────

@client_required
def dashboard(request):
    client = Client.objects.get(id=request.session['client_id'])

    token_error     = not client.token_valid
    total_messages  = MessageLog.objects.filter(client=client).count()
    inbound         = MessageLog.objects.filter(client=client, direction='inbound').count()
    outbound        = MessageLog.objects.filter(client=client, direction='outbound').count()
    active_rules    = AutoReplyRule.objects.filter(client=client, is_active=True).count()
    recent_messages = MessageLog.objects.filter(client=client).order_by('-timestamp')[:5]

    days_left = None
    if client.subscription_end:
        days_left = (client.subscription_end - date.today()).days
    show_renewal_warning = days_left is not None and days_left <= 7

    limits   = get_plan_limits(client.plan)
    ai_limit = limits["ai_replies"]
    ai_used  = client.ai_replies_used or 0

    return render(request, 'core/dashboard.html', {
        'client':               client,
        'token_error':          token_error,
        'total_messages':       total_messages,
        'inbound':              inbound,
        'outbound':             outbound,
        'active_rules':         active_rules,
        'recent_messages':      recent_messages,
        'days_left':            days_left,
        'show_renewal_warning': show_renewal_warning,
        'ai_used':              ai_used,
        'ai_limit':             '∞' if ai_limit == float('inf') else ai_limit,
        'plan_limits':          limits,
    })


# ─────────────────────────────────────────────
# MESSAGE HISTORY
# ─────────────────────────────────────────────

@client_required
def message_history(request):
    client      = Client.objects.get(id=request.session['client_id'])
    messages_qs = MessageLog.objects.filter(client=client).order_by('-timestamp')

    paginator     = Paginator(messages_qs, 20)
    page          = request.GET.get('page', 1)
    messages_list = paginator.get_page(page)

    return render(request, 'core/messages.html', {
        'client':        client,
        'messages_list': messages_list,
        'paginator':     paginator,
    })


# ─────────────────────────────────────────────
# AUTO REPLY RULES
# ─────────────────────────────────────────────

@client_required
def rules(request):
    client = Client.objects.get(id=request.session['client_id'])
    limits = get_plan_limits(client.plan)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            current_count = AutoReplyRule.objects.filter(client=client).count()
            max_rules     = limits["max_rules"]

            if max_rules != float('inf') and current_count >= max_rules:
                messages.error(
                    request,
                    f'Your {client.plan.title()} plan allows max {int(max_rules)} rules. '
                    f'Upgrade to Growth for unlimited rules.'
                )
                return redirect('rules')

            keyword  = request.POST.get('trigger_keyword', '').lower().strip()
            response = request.POST.get('response_text', '').strip()
            if keyword and response:
                AutoReplyRule.objects.create(
                    client=client,
                    trigger_keyword=keyword,
                    response_text=response
                )
                messages.success(request, 'Rule added successfully!')

        elif action == 'delete':
            rule_id = request.POST.get('rule_id')
            AutoReplyRule.objects.filter(id=rule_id, client=client).delete()
            messages.success(request, 'Rule deleted!')

        elif action == 'toggle':
            rule_id = request.POST.get('rule_id')
            rule    = AutoReplyRule.objects.get(id=rule_id, client=client)
            rule.is_active = not rule.is_active
            rule.save()

        return redirect('rules')

    all_rules     = AutoReplyRule.objects.filter(client=client).order_by('-created_at')
    current_count = all_rules.count()
    max_rules     = limits["max_rules"]

    paginator  = Paginator(all_rules, 15)
    page       = request.GET.get('page', 1)
    rules_page = paginator.get_page(page)

    return render(request, 'core/rules.html', {
        'client':        client,
        'rules':         rules_page,
        'current_count': current_count,
        'max_rules':     '∞' if max_rules == float('inf') else max_rules,
        'at_limit':      max_rules != float('inf') and current_count >= max_rules,
        'paginator':     paginator,
    })


# ─────────────────────────────────────────────
# PROFILE & TOKEN MANAGEMENT
# ─────────────────────────────────────────────

@client_required
def profile(request):
    client = Client.objects.get(id=request.session['client_id'])
    return render(request, 'core/profile.html', {'client': client})


@client_required
def update_token(request):
    if request.method == 'POST':
        client          = Client.objects.get(id=request.session['client_id'])
        access_token    = request.POST.get('access_token', '').strip()
        phone_number_id = request.POST.get('phone_number_id', '').strip()

        if not access_token:
            messages.error(request, 'Access token cannot be empty.')
            return redirect('profile')

        try:
            url      = f"https://graph.facebook.com/v19.0/{phone_number_id or client.phone_number_id}"
            headers  = {"Authorization": f"Bearer {access_token}"}
            response = http_requests.get(url, headers=headers, timeout=10)
            result   = response.json()

            if "error" in result:
                messages.error(
                    request,
                    f'Token test failed: {result["error"].get("message", "Invalid token")}. '
                    f'Token was NOT saved.'
                )
                return redirect('profile')

            # Check if new phone_number_id is already taken by another account
            if phone_number_id and phone_number_id != client.phone_number_id:
                existing = Client.objects.filter(
                    phone_number_id=phone_number_id
                ).exclude(id=client.id).first()
                if existing:
                    messages.error(
                        request,
                        'That Phone Number ID is already registered to another account. '
                        'Token was NOT saved.'
                    )
                    return redirect('profile')

            client.access_token = access_token
            if phone_number_id:
                client.phone_number_id = phone_number_id
            client.token_valid = True
            client.save()
            messages.success(request, '✅ Token updated and verified successfully!')

        except Exception as e:
            messages.error(request, f'Could not verify token: {str(e)}')

    return redirect('profile')


@client_required
def test_connection(request):
    if request.method == 'POST':
        client = Client.objects.get(id=request.session['client_id'])
        try:
            url      = f"https://graph.facebook.com/v19.0/{client.phone_number_id}"
            headers  = {"Authorization": f"Bearer {client.access_token}"}
            response = http_requests.get(url, headers=headers, timeout=10)
            result   = response.json()

            if "error" in result:
                client.token_valid = False
                client.save()
                return JsonResponse({
                    'success': False,
                    'error':   result['error'].get('message', 'Unknown error')
                })

            client.token_valid = True
            client.save()
            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


# ─────────────────────────────────────────────
# CONTACTS
# ─────────────────────────────────────────────

def clean_phone_number(phone):
    phone = re.sub(r'[^0-9]', '', str(phone))
    if phone.startswith('0') and len(phone) == 11:
        phone = '234' + phone[1:]
    phone = phone.lstrip('+')
    return phone if len(phone) >= 10 else None


@client_required
def contacts(request):
    client = Client.objects.get(id=request.session['client_id'])
    limits = get_plan_limits(client.plan)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            current_count = Contact.objects.filter(client=client).count()
            max_contacts  = limits["max_contacts"]

            if max_contacts != float('inf') and current_count >= max_contacts:
                messages.error(
                    request,
                    f'Your {client.plan.title()} plan allows max {int(max_contacts)} contacts. '
                    f'Upgrade to Growth for unlimited contacts.'
                )
                return redirect('contacts')

            name  = request.POST.get('name', '').strip()
            phone = clean_phone_number(request.POST.get('phone_number', ''))
            if name and phone:
                Contact.objects.get_or_create(
                    client=client,
                    phone_number=phone,
                    defaults={'name': name}
                )
                messages.success(request, 'Contact added!')

        elif action == 'delete':
            contact_id = request.POST.get('contact_id')
            Contact.objects.filter(id=contact_id, client=client).delete()
            messages.success(request, 'Contact deleted!')

        return redirect('contacts')

    all_contacts = Contact.objects.filter(client=client).order_by('-created_at')
    max_contacts = limits["max_contacts"]

    paginator     = Paginator(all_contacts, 25)
    page          = request.GET.get('page', 1)
    contacts_page = paginator.get_page(page)

    return render(request, 'core/contacts.html', {
        'client':          client,
        'contacts':        contacts_page,
        'total_contacts':  all_contacts.count(),
        'active_contacts': all_contacts.filter(opted_out=False).count(),
        'opted_out':       all_contacts.filter(opted_out=True).count(),
        'max_contacts':    '∞' if max_contacts == float('inf') else max_contacts,
        'at_limit':        max_contacts != float('inf') and all_contacts.count() >= max_contacts,
        'paginator':       paginator,
    })


# ─────────────────────────────────────────────
# BROADCAST
# ─────────────────────────────────────────────

@client_required
def broadcast(request):
    client = Client.objects.get(id=request.session['client_id'])
    limits = get_plan_limits(client.plan)

    if not limits["broadcast"]:
        messages.error(
            request,
            'Broadcasts are available on Growth and Pro plans. '
            'Upgrade your subscription to unlock this feature.'
        )
        return redirect('renew')

    contacts_count = Contact.objects.filter(client=client).count()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'broadcast':
            title         = request.POST.get('title')
            template_name = request.POST.get('template_name')

            token_response = http_requests.post(
                'http://localhost:8000/auth/login',
                data={
                    'username': client.email,
                    'password': request.POST.get('password')
                }
            )

            if token_response.status_code == 200:
                token = token_response.json().get('access_token')
                broadcast_response = http_requests.post(
                    'http://localhost:8000/broadcast/broadcast',
                    params={'title': title, 'template_name': template_name},
                    headers={'Authorization': f'Bearer {token}'}
                )
                if broadcast_response.status_code == 200:
                    messages.success(request, f'Broadcast "{title}" started successfully!')
                else:
                    messages.error(request, f'Broadcast failed: {broadcast_response.json().get("detail")}')
            else:
                messages.error(request, 'Authentication failed. Please try again.')

            return redirect('broadcast')

    all_broadcasts  = Broadcast.objects.filter(client=client).order_by('-created_at')

    paginator       = Paginator(all_broadcasts, 10)
    page            = request.GET.get('page', 1)
    broadcasts_page = paginator.get_page(page)

    return render(request, 'core/broadcast.html', {
        'client':         client,
        'broadcasts':     broadcasts_page,
        'contacts_count': contacts_count,
        'paginator':      paginator,
    })


# ─────────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────────

@client_required
def analytics(request):
    client = Client.objects.get(id=request.session['client_id'])

    from django.utils import timezone
    fourteen_days_ago = timezone.now() - timedelta(days=14)

    daily_messages = (
        MessageLog.objects
        .filter(client=client, timestamp__gte=fourteen_days_ago)
        .annotate(date=TruncDate('timestamp'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    inbound_messages = MessageLog.objects.filter(
        client=client, direction='inbound'
    ).values_list('message_text', flat=True)

    all_rules     = AutoReplyRule.objects.filter(client=client)
    keyword_stats = []
    for rule in all_rules:
        count = sum(1 for msg in inbound_messages if rule.trigger_keyword in msg.lower())
        keyword_stats.append({'keyword': rule.trigger_keyword, 'count': count})
    keyword_stats.sort(key=lambda x: x['count'], reverse=True)

    total            = MessageLog.objects.filter(client=client).count()
    inbound          = MessageLog.objects.filter(client=client, direction='inbound').count()
    outbound         = MessageLog.objects.filter(client=client, direction='outbound').count()
    unique_customers = MessageLog.objects.filter(
        client=client, direction='inbound'
    ).values('sender_number').distinct().count()

    return render(request, 'core/analytics.html', {
        'client':           client,
        'total':            total,
        'inbound':          inbound,
        'outbound':         outbound,
        'unique_customers': unique_customers,
        'chart_labels':     json.dumps([str(d['date']) for d in daily_messages]),
        'chart_data':       json.dumps([d['count'] for d in daily_messages]),
        'keyword_stats':    keyword_stats[:5],
    })


# ─────────────────────────────────────────────
# BUSINESS HOURS
# ─────────────────────────────────────────────

@client_required
def business_hours(request):
    client = Client.objects.get(id=request.session['client_id'])

    days = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')
    ]

    if request.method == 'POST':
        BusinessHours.objects.filter(client=client).delete()
        has_error = False

        for day_num, day_name in days:
            is_open    = request.POST.get(f'is_open_{day_num}') == 'on'
            is_allday  = request.POST.get(f'is_allday_{day_num}') == 'on'
            open_time  = request.POST.get(f'open_time_{day_num}', '').strip()
            close_time = request.POST.get(f'close_time_{day_num}', '').strip()

            if is_open:
                if is_allday:
                    open_time  = '00:00'
                    close_time = '23:59'
                else:
                    if not open_time or not close_time:
                        messages.error(request, f'{day_name} is marked open but missing open or close time.')
                        has_error = True
                        continue
                    if open_time == close_time:
                        messages.error(request, f'{day_name} open and close time cannot be the same.')
                        has_error = True
                        continue

            BusinessHours.objects.create(
                client=client,
                day_of_week=day_num,
                open_time=open_time   if open_time  else '00:00',
                close_time=close_time if close_time else '00:00',
                is_open=is_open
            )

        if not has_error:
            messages.success(request, 'Business hours updated successfully!')
        return redirect('business_hours')

    existing_hours = {
        h.day_of_week: h
        for h in BusinessHours.objects.filter(client=client)
    }

    days_data = []
    for day_num, day_name in days:
        hour      = existing_hours.get(day_num)
        is_allday = hour and hour.open_time == '00:00' and hour.close_time == '23:59'
        days_data.append({
            'day_num':    day_num,
            'day_name':   day_name,
            'is_open':    hour.is_open    if hour else day_num < 5,
            'open_time':  hour.open_time  if hour else '09:00',
            'close_time': hour.close_time if hour else '18:00',
            'is_allday':  is_allday,
        })

    return render(request, 'core/business_hours.html', {
        'client':    client,
        'days_data': days_data
    })


# ─────────────────────────────────────────────
# PRODUCTS
# ─────────────────────────────────────────────

@client_required
def products(request):
    client = Client.objects.get(id=request.session['client_id'])
    limits = get_plan_limits(client.plan)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            current_count = Product.objects.filter(client=client).count()
            max_products  = limits["max_products"]

            if max_products != float('inf') and current_count >= max_products:
                messages.error(
                    request,
                    f'Your {client.plan.title()} plan allows max {int(max_products)} products. '
                    f'Upgrade to Growth for unlimited products.'
                )
                return redirect('products')

            name        = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            price       = request.POST.get('price', '').strip()
            category    = request.POST.get('category', '').strip()
            keyword     = request.POST.get('keyword', '').lower().strip()
            image_file  = request.FILES.get('image_file')

            if name and price and keyword:
                image_url       = None
                image_public_id = None

                if image_file:
                    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
                    if image_file.content_type not in allowed_types:
                        messages.error(request, 'Please upload a JPG, PNG or WEBP image.')
                        return redirect('products')

                    upload_result = upload_image(image_file)
                    if upload_result:
                        image_url       = upload_result['url']
                        image_public_id = upload_result['public_id']
                    else:
                        messages.error(request, 'Image upload failed. Please try again.')
                        return redirect('products')

                Product.objects.create(
                    client=client,
                    name=name,
                    description=description,
                    price=price,
                    image_url=image_url,
                    image_public_id=image_public_id,
                    category=category if category else None,
                    keyword=keyword
                )
                messages.success(request, f'Product "{name}" added successfully!')

        elif action == 'delete':
            product_id = request.POST.get('product_id')
            product    = Product.objects.filter(id=product_id, client=client).first()
            if product:
                if product.image_public_id:
                    delete_image(product.image_public_id)
                product.delete()
                messages.success(request, 'Product deleted!')

        elif action == 'toggle':
            product_id = request.POST.get('product_id')
            product    = Product.objects.get(id=product_id, client=client)
            product.is_active = not product.is_active
            product.save()
            messages.success(request, 'Product status updated!')

        return redirect('products')

    all_products  = Product.objects.filter(client=client).order_by('category', 'name')
    current_count = all_products.count()
    max_products  = limits["max_products"]

    paginator     = Paginator(all_products, 12)
    page          = request.GET.get('page', 1)
    products_page = paginator.get_page(page)

    return render(request, 'core/products.html', {
        'client':         client,
        'products':       products_page,
        'total_products': current_count,
        'max_products':   '∞' if max_products == float('inf') else max_products,
        'at_limit':       max_products != float('inf') and current_count >= max_products,
        'paginator':      paginator,
    })


# ─────────────────────────────────────────────
# MESSAGE TEMPLATES
# ─────────────────────────────────────────────

@client_required
def message_templates(request):
    client      = Client.objects.get(id=request.session['client_id'])
    template, _ = MessageTemplate.objects.get_or_create(client=client)

    if request.method == 'POST':
        template.welcome_message  = request.POST.get('welcome_message', '').strip()
        template.menu_message     = request.POST.get('menu_message', '').strip()
        template.closed_message   = request.POST.get('closed_message', '').strip()
        template.handoff_message  = request.POST.get('handoff_message', '').strip()
        template.fallback_message = request.POST.get('fallback_message', '').strip()
        template.save()
        messages.success(request, 'Message templates saved successfully!')
        return redirect('message_templates')

    all_rules    = AutoReplyRule.objects.filter(client=client, is_active=True)
    all_products = Product.objects.filter(client=client, is_active=True)

    categories = {}
    for product in all_products:
        cat = product.category or "Products"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(product)

    menu_suggestion  = f"📋 *{client.business_name} Menu*\n\n"
    if categories:
        for cat in categories:
            menu_suggestion += f"🛍️ Type *{cat.lower()}* - Browse {cat}\n"
    for rule in all_rules:
        menu_suggestion += f"▪️ Type *{rule.trigger_keyword}* - {rule.response_text[:40]}\n"
    menu_suggestion += "👤 Type *human* - Talk to an agent\n"
    menu_suggestion += "\nType *menu* anytime to see this again."

    welcome_suggestion  = f"👋 Welcome to *{client.business_name}*!\n\n"
    welcome_suggestion += "We're glad you reached out.\n\n"
    for cat in categories:
        welcome_suggestion += f"🛍️ Type *{cat.lower()}* - Browse {cat}\n"
    for rule in all_rules:
        welcome_suggestion += f"▪️ Type *{rule.trigger_keyword}* - Info\n"
    welcome_suggestion += "👤 Type *human* - Speak with an agent\n\n"
    welcome_suggestion += "Just type any keyword to get started! 😊"

    defaults = {
        'welcome_message': welcome_suggestion,
        'menu_message':    menu_suggestion,
        'closed_message': (
            "🕐 *We're currently closed.*\n\n"
            "Our team is not available right now.\n"
            "Type *hours* to see our working hours."
        ),
        'handoff_message': (
            "👤 *Connecting you to an agent...*\n\n"
            "Someone from our team will respond shortly."
        ),
        'fallback_message': (
            "🤔 Sorry, I didn't quite understand that.\n\n"
            "Type *menu* to see available options."
        ),
    }

    return render(request, 'core/message_templates.html', {
        'client':       client,
        'template':     template,
        'defaults':     defaults,
        'rules':        all_rules,
        'products':     all_products,
        'categories':   categories,
        'has_rules':    all_rules.exists(),
        'has_products': all_products.exists(),
    })


# ─────────────────────────────────────────────
# PASSWORD RESET
# ─────────────────────────────────────────────

def forgot_password(request):
    if request.method == 'POST':
        email  = request.POST.get('email', '').strip().lower()
        client = Client.objects.filter(email=email).first()

        if client:
            PasswordResetToken.objects.filter(client=client, used=False).delete()

            token      = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=1)

            PasswordResetToken.objects.create(
                client=client,
                token=token,
                expires_at=expires_at
            )

            reset_link = request.build_absolute_uri(f'/reset-password/{token}/')
            send_password_reset_email(client.email, client.business_name, reset_link)

        return render(request, 'core/forgot_password.html', {
            'sent':  True,
            'email': email
        })

    return render(request, 'core/forgot_password.html')


def reset_password(request, token):
    reset_token = PasswordResetToken.objects.filter(token=token).first()

    if not reset_token or not reset_token.is_valid():
        return render(request, 'core/reset_password.html', {'invalid': True})

    if request.method == 'POST':
        password = request.POST.get('password', '')
        confirm  = request.POST.get('confirm_password', '')

        if len(password) < 6:
            return render(request, 'core/reset_password.html', {
                'token': token,
                'error': 'Password must be at least 6 characters.'
            })

        if password != confirm:
            return render(request, 'core/reset_password.html', {
                'token': token,
                'error': 'Passwords do not match.'
            })

        reset_token.client.hashed_password = pwd_context.hash(password)
        reset_token.client.save()
        reset_token.used = True
        reset_token.save()

        return render(request, 'core/reset_password.html', {'success': True})

    return render(request, 'core/reset_password.html', {'token': token})


# ─────────────────────────────────────────────
# SUBSCRIPTION RENEWAL
# ─────────────────────────────────────────────

@client_required

def renew(request):
    client     = Client.objects.get(id=request.session['client_id'])
    plans_dict = get_plans_from_db()

    days_left = None
    if client.subscription_end:
        days_left = (client.subscription_end - date.today()).days

    if request.method == 'POST':
        plan        = request.POST.get('plan', client.plan)
        months      = int(request.POST.get('months', 1))
        plan_obj    = plans_dict.get(plan)
        base_amount = plan_obj.price_kobo if plan_obj else PLAN_PRICES.get(plan, 800000)

        # ── Calculate discounted amount ──
        if months == 3:
            discount_pct = getattr(plan_obj, 'discount_3_months', 10) if plan_obj else 10
        elif months == 6:
            discount_pct = getattr(plan_obj, 'discount_6_months', 15) if plan_obj else 15
        elif months == 12:
            discount_pct = getattr(plan_obj, 'discount_12_months', 20) if plan_obj else 20
        else:
            discount_pct = 0

        total_amount = int(base_amount * months * (1 - discount_pct / 100))

        try:
            response = http_requests.post(
                "https://api.paystack.co/transaction/initialize",
                headers={
                    "Authorization": f"Bearer {os.getenv('PAYSTACK_SECRET_KEY')}",
                    "Content-Type": "application/json"
                },
                json={
                    "email":        client.email,
                    "amount":       total_amount,
                    "currency":     "NGN",
                    "callback_url": f"{os.getenv('BASE_URL')}/payment/renew-verify/",
                    "metadata": {
                        "client_id":  client.id,
                        "plan":       plan,
                        "months":     months,
                        "email":      client.email,
                        "is_renewal": True
                    },
                    "channels": ["card", "bank", "ussd", "bank_transfer", "mobile_money"]
                }
            )
            data = response.json()

            if data["status"]:
                return redirect(data["data"]["authorization_url"])
            else:
                return render(request, 'core/renew.html', {
                    'client':    client,
                    'days_left': days_left,
                    'error':     'Payment initialization failed.',
                    'starter':   plans_dict.get('starter'),
                    'growth':    plans_dict.get('growth'),
                    'pro':       plans_dict.get('pro'),
                })

        except Exception as e:
            return render(request, 'core/renew.html', {
                'client':    client,
                'days_left': days_left,
                'error':     str(e),
                'starter':   plans_dict.get('starter'),
                'growth':    plans_dict.get('growth'),
                'pro':       plans_dict.get('pro'),
            })

    return render(request, 'core/renew.html', {
        'client':    client,
        'days_left': days_left,
        'starter':   plans_dict.get('starter'),
        'growth':    plans_dict.get('growth'),
        'pro':       plans_dict.get('pro'),
    })

@client_required
def update_ai_description(request):
    if request.method == 'POST':
        client = Client.objects.get(id=request.session['client_id'])

        # Only Growth and Pro can use AI
        if client.plan == 'starter':
            messages.error(request, 'AI Smart Replies require Growth or Pro plan.')
            return redirect('profile')

        description = request.POST.get('business_description', '').strip()

        # Enforce max length
        if len(description) > 2000:
            messages.error(request, 'Description too long. Maximum 2000 characters.')
            return redirect('profile')

        client.business_description = description
        client.save()
        messages.success(request, '✅ AI description saved! Your bot will now use this context.')
        return redirect('profile')

    return redirect('profile')


def _unsubscribe_meta_webhook(client):
    """Unsubscribes client WhatsApp number from Meta webhooks before deletion."""
    try:
        if not client.waba_id or not client.access_token:
            logger.info(
                f"[_unsubscribe_meta_webhook] Skipping {client.business_name} "
                f"— no WABA ID or token"
            )
            return

        url      = f"https://graph.facebook.com/v19.0/{client.waba_id}/subscribed_apps"
        headers  = {"Authorization": f"Bearer {client.access_token}"}
        response = http_requests.delete(url, headers=headers, timeout=10)
        result   = response.json()

        if result.get("success"):
            logger.info(
                f"[_unsubscribe_meta_webhook] Unsubscribed {client.business_name} "
                f"(WABA: {client.waba_id})"
            )
        else:
            # Not a hard failure — Meta may have already removed it
            logger.warning(
                f"[_unsubscribe_meta_webhook] Unexpected response for "
                f"{client.business_name}: {result}"
            )

    except Exception as e:
        # Never block account deletion because of a Meta API issue
        logger.error(
            f"[_unsubscribe_meta_webhook] Failed for {client.business_name}: {e}",
            exc_info=True
        )


@client_required
def delete_account(request):
    if request.method == 'POST':
        client   = Client.objects.get(id=request.session['client_id'])
        password = request.POST.get('password', '').strip()
        confirm  = request.POST.get('confirm_text', '').strip()

        # ── Validate confirmation phrase ──
        if confirm != 'DELETE':
            messages.error(request, '❌ Please type DELETE exactly to confirm.')
            return redirect('profile')

        # ── Validate password ──
        if not pwd_context.verify(password, client.hashed_password):
            messages.error(request, '❌ Incorrect password. Account not deleted.')
            return redirect('profile')

        try:
            business_name = client.business_name
            client_email  = client.email

            # ── 1. Unsubscribe Meta webhook (must happen before deletion) ──
            _unsubscribe_meta_webhook(client)

            # ── 2. Delete all related data in order ──
            # (Django cascades handle most, but being explicit)
            MessageLog.objects.filter(client=client).delete()
            AutoReplyRule.objects.filter(client=client).delete()
            Contact.objects.filter(client=client).delete()
            Broadcast.objects.filter(client=client).delete()
            BusinessHours.objects.filter(client=client).delete()

            # Delete product images from Cloudinary
            products = Product.objects.filter(client=client)
            for product in products:
                if product.image_public_id:
                    try:
                        delete_image(product.image_public_id)
                    except Exception:
                        pass
            products.delete()

            MessageTemplate.objects.filter(client=client).delete()
            PasswordResetToken.objects.filter(client=client).delete()
            PaymentLog.objects.filter(client=client).delete()

            # Delete client record itself
            client.delete()

            # ── Clear session ──
            request.session.flush()

            logger.info(f"[delete_account] Deleted: {business_name} ({client_email})")
            return redirect('/account-deleted/')

        except Exception as e:
            logger.error(f"[delete_account] Error: {e}", exc_info=True)
            messages.error(request, 'Something went wrong. Please contact support.')
            return redirect('profile')

    return redirect('profile')


def account_deleted(request):
    """Simple confirmation page shown after account deletion."""
    return render(request, 'core/account_deleted.html')


def support(request):
    """Contact / support form — sends message to admin via Resend."""
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        email      = request.POST.get('email', '').strip()
        phone      = request.POST.get('phone', '').strip()
        subject    = request.POST.get('subject', 'General Enquiry').strip()
        message    = request.POST.get('message', '').strip()

        if not all([first_name, email, message]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'core/support.html')

        admin_email = os.getenv('ADMIN_NOTIFY_EMAIL')
        if admin_email:
            try:
                import requests as http_requests
                api_key    = os.getenv('RESEND_API_KEY')
                from_email = os.getenv('MAIL_FROM', 'noreply@botmart.app')
                from_name  = os.getenv('MAIL_FROM_NAME', 'BotMart')

                html = f"""
                <h2 style="color:#065f46;">New Contact Form Submission</h2>
                <table style="border-collapse:collapse;width:100%;font-family:Arial,sans-serif;">
                    <tr><td style="padding:8px;border:1px solid #e5e7eb;font-weight:600;background:#f9fafb;">Name</td>
                        <td style="padding:8px;border:1px solid #e5e7eb;">{first_name} {last_name}</td></tr>
                    <tr><td style="padding:8px;border:1px solid #e5e7eb;font-weight:600;background:#f9fafb;">Email</td>
                        <td style="padding:8px;border:1px solid #e5e7eb;"><a href="mailto:{email}">{email}</a></td></tr>
                    <tr><td style="padding:8px;border:1px solid #e5e7eb;font-weight:600;background:#f9fafb;">Phone</td>
                        <td style="padding:8px;border:1px solid #e5e7eb;">{phone or 'Not provided'}</td></tr>
                    <tr><td style="padding:8px;border:1px solid #e5e7eb;font-weight:600;background:#f9fafb;">Subject</td>
                        <td style="padding:8px;border:1px solid #e5e7eb;">{subject}</td></tr>
                    <tr><td style="padding:8px;border:1px solid #e5e7eb;font-weight:600;background:#f9fafb;">Message</td>
                        <td style="padding:8px;border:1px solid #e5e7eb;">{message.replace(chr(10), '<br>')}</td></tr>
                </table>
                <p style="color:#6b7280;font-size:12px;margin-top:20px;">
                    Sent from BotMart contact form at botmart.app
                </p>
                """

                if api_key:
                    http_requests.post(
                        "https://api.resend.com/emails",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "from": f"{from_name} <{from_email}>",
                            "to": [admin_email],
                            "reply_to": email,
                            "subject": f"[BotMart Support] {subject} — {first_name} {last_name}",
                            "html": html,
                        },
                        timeout=15
                    )
            except Exception as e:
                logger.error(f"[support] Email failed: {e}", exc_info=True)

        messages.success(
            request,
            f"Thanks {first_name}! Your message has been sent. We\'ll reply within 24 hours."
        )
        return redirect('support')

    return render(request, 'core/support.html')





@csrf_exempt
def paystack_webhook(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'ignored'})

    # ── Verify Paystack signature ──
    secret    = os.getenv('PAYSTACK_SECRET_KEY', '')
    signature = request.META.get('HTTP_X_PAYSTACK_SIGNATURE', '')
    computed  = hmac.new(
        secret.encode('utf-8'),
        request.body,
        digestmod=hashlib.sha512
    ).hexdigest()

    if signature != computed:
        print(f"[paystack_webhook] Invalid signature — possible fake request")
        return JsonResponse({'status': 'invalid signature'}, status=400)

    try:
        payload = json.loads(request.body)
        event   = payload.get('event')

        print(f"[paystack_webhook] Event received: {event}")

        if event == 'charge.success':
            data     = payload['data']
            metadata = data.get('metadata', {})

            client_id  = metadata.get('client_id')
            plan       = metadata.get('plan', 'starter')
            months     = int(metadata.get('months', 1))
            is_renewal = metadata.get('is_renewal', False)
            reference  = data.get('reference')
            amount     = data.get('amount')

            if not client_id:
                print(f"[paystack_webhook] No client_id in metadata")
                return JsonResponse({'status': 'missing client_id'}, status=400)

            # ── Skip if already processed ──
            if PaymentLog.objects.filter(reference=reference).exists():
                print(f"[paystack_webhook] Already processed: {reference}")
                return JsonResponse({'status': 'already processed'})

            client = Client.objects.get(id=client_id)

            today = date.today()
            days  = months * 30 if months < 12 else 365

            if is_renewal:
                base = max(client.subscription_end, today) if client.subscription_end else today
                is_renewal = str(metadata.get('is_renewal', 'false')).lower() == 'true'
            else:
                base = today

            client.plan                = plan
            client.payment_status      = 'paid'
            client.payment_reference   = reference
            client.subscription_start  = today
            client.subscription_end    = base + timedelta(days=days)
            client.grace_period_end    = base + timedelta(days=days + 7)
            client.subscription_months = months
            client.reminder_7_sent     = False
            client.reminder_3_sent     = False
            client.is_active           = True
            client.save()

            PaymentLog.objects.create(
                client             = client,
                reference          = reference,
                amount_kobo        = amount,
                plan               = plan,
                months             = months,
                is_renewal         = is_renewal,
                subscription_start = today,
                subscription_end   = client.subscription_end,
            )

            print(f"[paystack_webhook] ✅ Payment recorded for {client.business_name} "
                  f"— {plan} x {months} month(s), ref: {reference}")

            # ── Notify admin ──
            amount_naira = amount // 100
            admin_url    = f"{os.getenv('BASE_URL', 'http://localhost:8001')}/admin/core/client/{client.id}/change/"
            if is_renewal:
                send_renewal_notification(
                    client_email  = client.email,
                    business_name = client.business_name,
                    plan          = plan,
                    months        = months,
                    amount_naira  = amount_naira,
                )
            else:
                send_new_client_notification(
                    client_email  = client.email,
                    business_name = client.business_name,
                    plan          = plan,
                    months        = months,
                    amount_naira  = amount_naira,
                    admin_url     = admin_url,
                )

    except Client.DoesNotExist:
        print(f"[paystack_webhook] Client not found for id: {client_id}")
        return JsonResponse({'status': 'client not found'}, status=404)
    except Exception as e:
        print(f"[paystack_webhook] Error: {e}")
        return JsonResponse({'status': 'error'}, status=500)

    return JsonResponse({'status': 'ok'})
def privacy(request):
    return render(request, 'core/privacy_policy.html')

def terms(request):
    return render(request, 'core/terms.html')   

def cookie(request):
    return render(request, 'core/cookie.html')

def support(request):
    return render(request, 'core/support.html')

def handler404(request, exception):
    return render(request, 'core/404.html', status=404)

def handler500(request):
    return render(request, 'core/500.html', status=500)


# ─────────────────────────────────────────────────────────────
# Add these to the BOTTOM of core/views.py
# ─────────────────────────────────────────────────────────────


def robots_txt(request):
    content = """User-agent: *
Allow: /
Allow: /register/
Allow: /login/
Allow: /privacy/
Allow: /terms/
Allow: /cookie/
Allow: /support/

# Block dashboard and private pages
Disallow: /dashboard/
Disallow: /profile/
Disallow: /rules/
Disallow: /products/
Disallow: /contacts/
Disallow: /broadcast/
Disallow: /analytics/
Disallow: /business-hours/
Disallow: /message-history/
Disallow: /message-templates/
Disallow: /renew/
Disallow: /admin/
Disallow: /payment/
Disallow: /paystack/
Disallow: /meta-setup/
Disallow: /subscribe/
Disallow: /pending/
Disallow: /delete-account/
Disallow: /reset-password/
Disallow: /account-deleted/

Sitemap: https://botmart.ng/sitemap.xml
"""
    return HttpResponse(content, content_type="text/plain")


def sitemap_xml(request):
    today = timezone.now().date().isoformat()
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">

  <url>
    <loc>https://botmart.ng/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>

  <url>
    <loc>https://botmart.ng/register/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>

  <url>
    <loc>https://botmart.ng/login/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>

  <url>
    <loc>https://botmart.ng/privacy/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.3</priority>
  </url>

  <url>
    <loc>https://botmart.ng/terms/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.3</priority>
  </url>

  <url>
    <loc>https://botmart.ng/support/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>

</urlset>"""
    return HttpResponse(content, content_type="application/xml")

# ─────────────────────────────────────────────────────────────
# 1. ADD this view to views.py  (replaces the old profile view
#    payment_logs section — profile.html no longer needs it)
# ─────────────────────────────────────────────────────────────


@client_required
def billing(request):
    client       = Client.objects.get(id=request.session['client_id'])
    payment_logs = PaymentLog.objects.filter(client=client).order_by('-paid_at')

    total_spent   = sum(p.amount_kobo for p in payment_logs)
    renewal_count = payment_logs.filter(is_renewal=True).count()

    days_left = None
    if client.subscription_end:
        days_left = (client.subscription_end - date.today()).days

    return render(request, 'core/billing.html', {
        'client':        client,
        'payment_logs':  payment_logs,
        'total_spent':   total_spent,
        'renewal_count': renewal_count,
        'days_left':     days_left,
    })





def _build_receipt_pdf(client, payment):
    """
    Generates a professional A4 receipt PDF.
    Returns a BytesIO buffer ready to be streamed.
    """

    # ── Data prep ──────────────────────────────────────────────
    amount_naira = payment.amount_kobo // 100
    months_map   = {1: '1 Month', 3: '3 Months', 6: '6 Months', 12: '12 Months'}
    months_label = months_map.get(payment.months, f'{payment.months} Months')
    paid_dt      = payment.paid_at
    paid_date    = paid_dt.strftime('%d %B %Y') if paid_dt else 'N/A'
    paid_time    = paid_dt.strftime('%I:%M %p') if paid_dt else ''
    sub_start    = payment.subscription_start.strftime('%d %B %Y') if payment.subscription_start else 'N/A'
    sub_end      = payment.subscription_end.strftime('%d %B %Y')   if payment.subscription_end   else 'N/A'
    ptype        = 'Subscription Renewal' if payment.is_renewal else 'New Subscription'
    today_str    = date.today().strftime('%d %B %Y')
    # Receipt number — deterministic from reference
    receipt_no   = f"BM-{payment.reference[-8:].upper()}"
    barcode_val  = f"BOTMART-{payment.reference.upper()}"

    plan_label_map = {'starter': 'Starter', 'growth': 'Growth', 'pro': 'Pro'}
    plan_label = plan_label_map.get(payment.plan, payment.plan.title())

    # ── Canvas setup ───────────────────────────────────────────
    buffer = io.BytesIO()
    c      = rl_canvas.Canvas(buffer, pagesize=A4)
    W, H   = A4
    M      = 18 * mm   # page margin

    # ── Colour tokens ──────────────────────────────────────────
    G_DARK   = colors.HexColor('#064e46')
    G_MID    = colors.HexColor('#075e54')
    G_BRIGHT = colors.HexColor('#25D366')
    G_MINT   = colors.HexColor('#a7f3d0')
    G_PALE   = colors.HexColor('#f0fdf4')
    G_BORDER = colors.HexColor('#d1fae5')
    INK      = colors.HexColor('#111827')
    GREY2    = colors.HexColor('#374151')
    GREY3    = colors.HexColor('#6b7280')
    GREY4    = colors.HexColor('#9ca3af')
    LGREY    = colors.HexColor('#f3f4f6')
    BORDER   = colors.HexColor('#e5e7eb')
    WHITE    = colors.white
    AMBER    = colors.HexColor("#0e0e0d")
    AMBER_BG = colors.HexColor('#fffbeb')

    plan_color_map = {
        'starter': colors.HexColor('#4b5563'),
        'growth':  colors.HexColor('#2563eb'),
        'pro':     colors.HexColor('#7c3aed'),
    }
    plan_color = plan_color_map.get(payment.plan, GREY3)

    # ── Helpers ────────────────────────────────────────────────
    def filled_rect(x, y, w, h, fill):
        c.saveState()
        c.setFillColor(fill)
        c.rect(x, y, w, h, fill=1, stroke=0)
        c.restoreState()

    def bordered_rect(x, y, w, h, fill, stroke, lw=0.5):
        c.saveState()
        c.setFillColor(fill)
        c.setStrokeColor(stroke)
        c.setLineWidth(lw)
        c.rect(x, y, w, h, fill=1, stroke=1)
        c.restoreState()

    def hline(x1, x2, y, color=BORDER, lw=0.4):
        c.saveState()
        c.setStrokeColor(color)
        c.setLineWidth(lw)
        c.line(x1, y, x2, y)
        c.restoreState()

    def label(x, y, text, size=8, bold=False, color=GREY3, align='left'):
        c.saveState()
        c.setFillColor(color)
        c.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
        if align == 'right':
            c.drawRightString(x, y, text)
        elif align == 'center':
            c.drawCentredString(x, y, text)
        else:
            c.drawString(x, y, text)
        c.restoreState()

    def row(y, left_text, right_text,
            left_size=9, right_size=9,
            left_bold=False, right_bold=False,
            left_color=GREY3, right_color=INK):
        """Draw a label-value pair across the full content width."""
        label(M + 3*mm,  y, left_text,  left_size,  left_bold,  left_color)
        label(W - M,     y, right_text, right_size, right_bold, right_color, align='right')

    # ══════════════════════════════════════════════════════════════
    # 1.  HEADER BAND
    # ══════════════════════════════════════════════════════════════
    HEADER_H = 72 * mm
    filled_rect(0, H - HEADER_H, W, HEADER_H, G_MID)

    # Subtle darker strip at very top (5 mm)
    filled_rect(0, H - 5*mm, W, 5*mm, G_DARK)

    # WhatsApp green accent strip (3 mm, left side)
    filled_rect(0, H - HEADER_H, 3*mm, HEADER_H, G_BRIGHT)

    # ── Logo block (top-left) ──
    label(M, H - 18*mm, 'BotMart', size=20, bold=True, color=WHITE)
    label(M, H - 25*mm, 'PAYMENT RECEIPT', size=7.5, color=G_MINT)

    # ── Receipt number (top-right) ──
    label(W - M, H - 18*mm, receipt_no, size=11, bold=True, color=WHITE, align='right')
    label(W - M, H - 25*mm, 'RECEIPT NO.', size=7, color=G_MINT, align='right')

    # ── Amount block (centred) ──
    label(W / 2, H - 40*mm, f'\u20a6{amount_naira:,}', size=34, bold=True, color=WHITE, align='center')
    # pill behind payment type
    pill_w = 52 * mm
    pill_x = W / 2 - pill_w / 2
    c.saveState()
    c.setFillColor(colors.HexColor('#ffffff1a'))
    c.roundRect(pill_x, H - 51*mm, pill_w, 7*mm, 3*mm, fill=1, stroke=0)
    c.restoreState()
    label(W / 2, H - 47.5*mm, ptype.upper(), size=7.5, color=G_MINT, align='center')

    # ── 3-column info strip (bottom of header) ──
    STRIP_H  = 16 * mm
    STRIP_Y  = H - HEADER_H
    col_w    = (W - 2 * M) / 3
    filled_rect(0, STRIP_Y, W, STRIP_H, G_DARK)

    cols = [
        ('REFERENCE',  payment.reference),
        ('DATE',       f'{paid_date}'),
        ('STATUS',     '✓  PAID'),
    ]
    for i, (col_lbl, col_val) in enumerate(cols):
        cx = M + i * col_w + col_w / 2
        label(cx, STRIP_Y + 10*mm, col_lbl, size=6.5, color=G_MINT, align='center')
        if col_val == '✓  PAID':
            # Green pill for PAID
            c.saveState()
            c.setFillColor(G_BRIGHT)
            c.roundRect(cx - 14*mm, STRIP_Y + 2*mm, 28*mm, 7*mm, 3*mm, fill=1, stroke=0)
            c.restoreState()
            label(cx, STRIP_Y + 4.5*mm, col_val, size=8, bold=True, color=WHITE, align='center')
        else:
            label(cx, STRIP_Y + 3.5*mm, col_val, size=8, bold=True, color=WHITE, align='center')

    # Vertical dividers inside strip
    for i in (1, 2):
        x = M + i * col_w
        c.saveState()
        c.setStrokeColor(colors.HexColor('#ffffff22'))
        c.setLineWidth(0.4)
        c.line(x, STRIP_Y + 2*mm, x, STRIP_Y + STRIP_H - 2*mm)
        c.restoreState()

    # ══════════════════════════════════════════════════════════════
    # 2.  BODY
    # ══════════════════════════════════════════════════════════════
    y = H - HEADER_H - 10*mm   # current y cursor (moves downward)

    def section_title(title):
        nonlocal y
        y -= 6*mm
        # small green pill label
        c.saveState()
        c.setFillColor(G_PALE)
        c.setStrokeColor(G_BORDER)
        c.setLineWidth(0.5)
        c.roundRect(M, y - 1.5*mm, len(title) * 4.8 + 8, 8.5, 3, fill=1, stroke=1)
        c.restoreState()
        label(M + 4, y + 1*mm, title, size=7.5, bold=True, color=G_MID)
        y -= 5*mm
        hline(M, W - M, y, color=BORDER, lw=0.4)
        y -= 5*mm

    def body_row(left, right, right_bold=False, right_color=INK):
        nonlocal y
        label(M + 3*mm, y, left,  size=9, color=GREY3)
        label(W - M,    y, right, size=9, bold=right_bold, color=right_color, align='right')
        y -= 7*mm

    def divider():
        nonlocal y
        y -= 1*mm
        hline(M, W - M, y, color=LGREY, lw=0.6)
        y -= 4*mm

    # ── Section A: Client ──
    section_title('CLIENT')
    body_row('Business Name',   client.business_name,    right_bold=True)
    body_row('Email Address',   client.email)
    body_row('WhatsApp Number', str(client.whatsapp_number) if client.whatsapp_number else 'N/A')

    divider()

    # ── Section B: Subscription ──
    section_title('SUBSCRIPTION')
    body_row('Plan',      plan_label, right_bold=True, right_color=plan_color)
    body_row('Duration',  months_label)
    body_row('Type',      ptype)
    body_row('Starts',    sub_start)
    body_row('Expires',   sub_end, right_bold=True)

    divider()

    # ── Section C: Payment ──
    section_title('PAYMENT')
    body_row('Processor',  'Paystack')
    body_row('Reference',  payment.reference)
    body_row('Paid On',    f'{paid_date}  {paid_time}')
    body_row('Amount',     f'\u20a6{amount_naira:,}', right_bold=True, right_color=G_MID)

    # ── Total box ──
    y -= 4*mm
    BOX_H = 14 * mm
    filled_rect(M, y - BOX_H + 4*mm, W - 2 * M, BOX_H, G_MID)
    label(M + 5*mm,  y - BOX_H + 9*mm,  'TOTAL AMOUNT PAID', size=8.5, color=G_MINT)
    label(W - M - 5*mm, y - BOX_H + 8*mm, f'\u20a6{amount_naira:,}', size=16, bold=True, color=WHITE, align='right')
    y -= BOX_H + 4*mm

    # ── Barcode section ──
    y -= 6*mm
    # light background strip
    filled_rect(M, y - 16*mm, W - 2*M, 22*mm, LGREY)

    # draw Code128 barcode
    try:
        bc = code128.Code128(
            barcode_val,
            barHeight = 10 * mm,
            barWidth  = 0.9,
            humanReadable = False,
        )
        bc_w = bc.width
        bc_x = W / 2 - bc_w / 2
        bc.drawOn(c, bc_x, y - 12*mm)
    except Exception:
        pass   # never crash if barcode fails

    label(W / 2, y - 14.5*mm, barcode_val, size=6.5, color=GREY4, align='center')
    label(W / 2, y + 3*mm,    'VERIFICATION CODE', size=6.5, bold=True, color=GREY3, align='center')
    y -= 22*mm

    # ── Notice box ──
    y -= 4*mm
    NOTICE_H = 13 * mm
    bordered_rect(M, y - NOTICE_H + 4*mm, W - 2*M, NOTICE_H, AMBER_BG,
                  colors.HexColor('#fde68a'), lw=0.5)
    # left amber bar
    filled_rect(M, y - NOTICE_H + 4*mm, 2.5, NOTICE_H, AMBER)
    label(M + 5*mm, y - NOTICE_H + 11*mm,
          'This is an auto-generated receipt and is valid without a signature.',
          size=7.5, color=colors.HexColor('#92400e'))
    label(M + 5*mm, y - NOTICE_H + 6*mm,
          'For billing enquiries contact: support@botmart.ng',
          size=7.5, color=GREY3)

    # ══════════════════════════════════════════════════════════════
    # 3.  FOOTER
    # ══════════════════════════════════════════════════════════════
    FOOTER_H = 16 * mm
    filled_rect(0, 0, W, FOOTER_H, LGREY)
    hline(0, W, FOOTER_H, color=BORDER, lw=0.5)

    label(W / 2, 10.5*mm, 'BotMart  ·  WhatsApp Automation Platform  ·  botmart.ng',
          size=7.5, bold=True, color=G_MID, align='center')
    label(W / 2, 6*mm,
          f'Generated on {today_str}  ·  Powered by Paystack',
          size=7, color=GREY4, align='center')
    label(W / 2, 2.5*mm,
          'This electronic receipt is issued under BotMart Terms of Service.',
          size=6.5, color=GREY4, align='center')

    # ── Page border (thin green rule on all sides) ──
    c.saveState()
    c.setStrokeColor(G_BRIGHT)
    c.setLineWidth(1.5)
    c.rect(3*mm, 3*mm, W - 6*mm, H - 6*mm, fill=0, stroke=1)
    c.restoreState()

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


@client_required
def view_receipt(request, reference):
    """Streams the receipt PDF inline (opens in browser tab)."""
    client = Client.objects.get(id=request.session['client_id'])
    try:
        payment = PaymentLog.objects.get(reference=reference, client=client)
    except PaymentLog.DoesNotExist:
        raise Http404

    buf      = _build_receipt_pdf(client, payment)
    filename = f"BotMart_Receipt_{payment.reference}.pdf"
    resp     = FileResponse(buf, content_type='application/pdf')
    resp['Content-Disposition'] = f'inline; filename="{filename}"'
    return resp


@client_required
def download_receipt(request, reference):
    """Forces the receipt PDF to download as a file."""
    client = Client.objects.get(id=request.session['client_id'])
    try:
        payment = PaymentLog.objects.get(reference=reference, client=client)
    except PaymentLog.DoesNotExist:
        raise Http404

    buf      = _build_receipt_pdf(client, payment)
    filename = f"BotMart_Receipt_{payment.reference}.pdf"
    resp     = FileResponse(buf, content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    return resp