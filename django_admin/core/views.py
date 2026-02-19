from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Client, AutoReplyRule, MessageLog
from django.db.models import Count
from django.db.models.functions import TruncDate
import json

def client_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        try:
            client = Client.objects.get(email=email)
            if pwd_context.verify(password, client.hashed_password):
                request.session['client_id'] = client.id
                request.session['client_name'] = client.business_name
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid email or password')
        except Client.DoesNotExist:
            messages.error(request, 'Invalid email or password')

    return render(request, 'core/login.html')


def client_logout(request):
    request.session.flush()
    return redirect('client_login')


def client_required(view_func):
    def wrapper(request, *args, **kwargs):
        if 'client_id' not in request.session:
            return redirect('client_login')
        return view_func(request, *args, **kwargs)
    return wrapper


@client_required
def dashboard(request):
    client = Client.objects.get(id=request.session['client_id'])
    total_messages = MessageLog.objects.filter(client=client).count()
    inbound = MessageLog.objects.filter(client=client, direction='inbound').count()
    outbound = MessageLog.objects.filter(client=client, direction='outbound').count()
    active_rules = AutoReplyRule.objects.filter(client=client, is_active=True).count()
    recent_messages = MessageLog.objects.filter(client=client).order_by('-timestamp')[:5]

    context = {
        'client': client,
        'total_messages': total_messages,
        'inbound': inbound,
        'outbound': outbound,
        'active_rules': active_rules,
        'recent_messages': recent_messages,
    }
    return render(request, 'core/dashboard.html', context)
@client_required
def message_history(request):
    client = Client.objects.get(id=request.session['client_id'])
    messages_list = MessageLog.objects.filter(client=client).order_by('-timestamp')[:100]
    return render(request, 'core/messages.html', {'client': client, 'messages_list': messages_list})


@client_required
def rules(request):
    client = Client.objects.get(id=request.session['client_id'])

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            keyword = request.POST.get('trigger_keyword', '').lower().strip()
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
            rule = AutoReplyRule.objects.get(id=rule_id, client=client)
            rule.is_active = not rule.is_active
            rule.save()

        return redirect('rules')

    all_rules = AutoReplyRule.objects.filter(client=client).order_by('-created_at')
    return render(request, 'core/rules.html', {'client': client, 'rules': all_rules})


@client_required
def profile(request):
    client = Client.objects.get(id=request.session['client_id'])
    return render(request, 'core/profile.html', {'client': client})

from .models import Client, AutoReplyRule, MessageLog, Contact, Broadcast
import requests as http_requests

@client_required
def contacts(request):
    client = Client.objects.get(id=request.session['client_id'])

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            name = request.POST.get('name', '').strip()
            phone = request.POST.get('phone_number', '').strip()
            if name and phone:
                Contact.objects.get_or_create(client=client, phone_number=phone, defaults={'name': name})
                messages.success(request, 'Contact added!')

        elif action == 'delete':
            contact_id = request.POST.get('contact_id')
            Contact.objects.filter(id=contact_id, client=client).delete()
            messages.success(request, 'Contact deleted!')

        return redirect('contacts')

    all_contacts = Contact.objects.filter(client=client).order_by('-created_at')
    return render(request, 'core/contacts.html', {'client': client, 'contacts': all_contacts})


@client_required
def broadcast(request):
    client = Client.objects.get(id=request.session['client_id'])
    contacts_count = Contact.objects.filter(client=client).count()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'broadcast':
            title = request.POST.get('title')
            template_name = request.POST.get('template_name')

            # First get a JWT token for this client
            token_response = http_requests.post(
                'http://localhost:8000/auth/login',
                data={
                    'username': client.email,
                    'password': request.POST.get('password')
                }
            )

            if token_response.status_code == 200:
                token = token_response.json().get('access_token')

                # Call FastAPI broadcast endpoint
                broadcast_response = http_requests.post(
                    f'http://localhost:8000/broadcast/broadcast',
                    params={
                        'title': title,
                        'template_name': template_name
                    },
                    headers={'Authorization': f'Bearer {token}'}
                )

                if broadcast_response.status_code == 200:
                    messages.success(request, f'Broadcast "{title}" started successfully!')
                else:
                    messages.error(request, f'Broadcast failed: {broadcast_response.json().get("detail")}')
            else:
                messages.error(request, 'Authentication failed. Please try again.')

            return redirect('broadcast')

    all_broadcasts = Broadcast.objects.filter(client=client).order_by('-created_at')
    return render(request, 'core/broadcast.html', {
        'client': client,
        'broadcasts': all_broadcasts,
        'contacts_count': contacts_count
    })


@client_required
def analytics(request):
    client = Client.objects.get(id=request.session['client_id'])

    # Messages per day (last 14 days)
    from datetime import datetime, timedelta
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

    # Most triggered keywords
    inbound_messages = MessageLog.objects.filter(
        client=client, direction='inbound'
    ).values_list('message_text', flat=True)

    rules = AutoReplyRule.objects.filter(client=client)
    keyword_stats = []
    for rule in rules:
        count = sum(1 for msg in inbound_messages if rule.trigger_keyword in msg.lower())
        keyword_stats.append({
            'keyword': rule.trigger_keyword,
            'count': count
        })
    keyword_stats.sort(key=lambda x: x['count'], reverse=True)

    # Overall stats
    total = MessageLog.objects.filter(client=client).count()
    inbound = MessageLog.objects.filter(client=client, direction='inbound').count()
    outbound = MessageLog.objects.filter(client=client, direction='outbound').count()
    unique_customers = MessageLog.objects.filter(
        client=client, direction='inbound'
    ).values('sender_number').distinct().count()

    chart_labels = [str(d['date']) for d in daily_messages]
    chart_data = [d['count'] for d in daily_messages]

    return render(request, 'core/analytics.html', {
        'client': client,
        'total': total,
        'inbound': inbound,
        'outbound': outbound,
        'unique_customers': unique_customers,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'keyword_stats': keyword_stats[:5],
    })