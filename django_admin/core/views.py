from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.core.paginator import Paginator
from datetime import date, datetime, timedelta
import json
import re
import os
import secrets

from passlib.context import CryptContext
import requests as http_requests

from .models import (
    Client, AutoReplyRule, MessageLog, Contact,
    Broadcast, BusinessHours, Product, MessageTemplate,
    PasswordResetToken, SubscriptionPlan
)
from .cloudinary_helper import upload_image, delete_image
from .email_helper import send_password_reset_email

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
        return view_func(request, *args, **kwargs)
    return wrapper


def client_login(request):
    if request.method == 'POST':
        email    = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '').strip()

        try:
            client = Client.objects.get(email=email)
            if pwd_context.verify(password, client.hashed_password):
                request.session['client_id']   = client.id
                request.session['client_name'] = client.business_name
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid email or password')
        except Client.DoesNotExist:
            messages.error(request, 'Invalid email or password')

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
        plan_obj = plans_dict.get(plan)
        amount   = plan_obj.price_kobo if plan_obj else PLAN_PRICES.get(plan, 800000)

        try:
            response = http_requests.post(
                "https://api.paystack.co/transaction/initialize",
                headers={
                    "Authorization": f"Bearer {os.getenv('PAYSTACK_SECRET_KEY')}",
                    "Content-Type": "application/json"
                },
                json={
                    "email":        client.email,
                    "amount":       amount,
                    "currency":     "NGN",
                    "callback_url": f"{os.getenv('BASE_URL')}/payment/verify/",
                    "metadata": {
                        "client_id": client.id,
                        "plan":      plan,
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
        plan     = request.POST.get('plan', client.plan)
        plan_obj = plans_dict.get(plan)
        amount   = plan_obj.price_kobo if plan_obj else PLAN_PRICES.get(plan, 800000)

        try:
            response = http_requests.post(
                "https://api.paystack.co/transaction/initialize",
                headers={
                    "Authorization": f"Bearer {os.getenv('PAYSTACK_SECRET_KEY')}",
                    "Content-Type": "application/json"
                },
                json={
                    "email":        client.email,
                    "amount":       amount,
                    "currency":     "NGN",
                    "callback_url": f"{os.getenv('BASE_URL')}/payment/renew-verify/",
                    "metadata": {
                        "client_id":  client.id,
                        "plan":       plan,
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