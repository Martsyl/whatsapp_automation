💬
BotMart
WhatsApp Automation Platform
Complete Technical README  •  Version 1.0  •  March 2026
FastAPI	Django 6	PostgreSQL	Celery + Redis	WhatsApp API

1. Project Overview
BotMart is a multi-tenant WhatsApp Automation SaaS platform that enables Nigerian businesses to automate customer interactions via WhatsApp. Built on top of the Meta (Facebook) WhatsApp Business API, the platform provides intelligent auto-replies, product catalogues, broadcast messaging, subscription management, and a full Django admin interface — all accessible through a clean web dashboard.

The system is split into two applications that share the same PostgreSQL database:
    • FastAPI:  FastAPI (app/) — the WhatsApp webhook engine, handles all real-time message processing
    • Django:  Django (django_admin/) — the web dashboard, admin panel, subscription billing, and email campaigns

2. Technology Stack
Layer	Technology
Webhook Engine	FastAPI (Python) — async, high performance
Admin Dashboard	Django 6.0 + Django Admin
Database	PostgreSQL (shared between FastAPI & Django)
ORM (FastAPI)	SQLAlchemy — declarative models
ORM (Django)	Django ORM — migrations managed
Background Tasks	Celery 5 + Redis — email campaigns, scheduled tasks
Task Scheduler	Celery Beat — periodic task dispatch
File Storage	Cloudinary — product images
Email	Gmail SMTP (dev) → Domain email / SendGrid (production)
Payments	Paystack — subscription billing (NGN)
AI Replies	Anthropic Claude API — smart AI customer replies
WhatsApp API	Meta Graph API v19.0 — WhatsApp Business
Tunneling (dev)	Ngrok — expose local server to Meta webhook
Server	Uvicorn (FastAPI) + Gunicorn (Django)

3. System Architecture
The two applications run on different ports and share the same database:

FastAPI  →  Port 8000  →  /webhook/   (WhatsApp messages)
Django   →  Port 8001  →  /admin/     (Dashboard & admin)
Ngrok    →  Tunnels port 8000 to public HTTPS URL for Meta
Redis    →  Port 6379  →  Celery broker & result backend
Celery   →  Worker + Beat processes for background email sending

Message Flow
When a WhatsApp message arrives, the following flow occurs:
    • Meta sends POST to ngrok URL → FastAPI /webhook/
    • FastAPI returns 200 OK immediately to Meta (prevents retry loops)
    • Message is processed in background via BackgroundTasks
    • Deduplication check — whatsapp_message_id prevents duplicate processing
    • Client identified by phone_number_id from Meta metadata
    • Subscription validity checked — expired clients get no reply
    • Contact auto-saved if first interaction
    • Business hours checked — closed message sent if outside hours
    • Welcome message sent to new users
    • Subsequent messages: rules → category → product → AI → fallback

4. Features Built
Feature	Description	Status
WhatsApp Webhook	Receives & processes real-time WhatsApp messages via Meta API	✅ Live
Deduplication	whatsapp_message_id prevents Meta retry duplicates	✅ Live
Auto-Reply Rules	Keyword-triggered custom responses, ordered by priority	✅ Live
Product Catalogue	Products with categories, keywords, prices, Cloudinary images	✅ Live
AI Smart Replies	Claude AI replies for Growth & Pro plan clients	✅ Live
AI Retry Logic	529 overload retry with 2-second wait before fallback	✅ Live
Business Hours	Per-day open/close times — closed message outside hours	✅ Live
Contact Management	Auto-save contacts, opt-out (STOP) and opt-in (START)	✅ Live
Human Handoff	Customer types 'human' → email alert sent to business owner	✅ Live
Broadcast Messaging	Send bulk messages to all contacts or selected groups	✅ Live
Message Templates	Customisable welcome, menu, closed, handoff, fallback messages	✅ Live
4-Step Registration	Business onboarding: details → Meta credentials → plan → payment	✅ Live
Subscription Plans	Starter / Growth / Pro — DB-driven pricing via SubscriptionPlan model	✅ Live
Paystack Payments	NGN subscription billing — webhook confirms payment	✅ Live
Plan Limits	AI reply limits enforced per plan — monthly reset	✅ Live
Renewal Reminders	7-day and 3-day email reminders before subscription expires	✅ Live
Grace Period	Clients get buffer after expiry before bot is paused	✅ Live
Analytics Dashboard	Message stats, contact counts, broadcast history	✅ Live
Email Campaigns	Bulk email to all/plan/selected clients with HTML template	✅ Live
Campaign Scheduling	Schedule campaigns for future — Celery Beat auto-dispatches	✅ Live
Campaign Progress	Real-time progress bar in admin — batches of 50, 1.5s delay	✅ Live
Password Reset	Secure token-based password reset via email	✅ Live
Email Templates	Professional dark-mode-safe HTML email design (all 4 types)	✅ Live
Pagination	All list views paginated: messages, contacts, broadcasts, rules, products	✅ Live
Token Error Detection	Flags invalid Meta access tokens automatically	✅ Live
Landing Page	Public marketing page with DB-driven pricing plans	✅ Live
Django Admin	Full admin panel for managing all clients, plans, campaigns	✅ Live

5. Project Structure
ALX_project/
├── app/                         # FastAPI application
│   ├── main.py                  # App entry point, router registration
│   ├── models.py                # SQLAlchemy models (shared with Django DB)
│   ├── database.py              # DB connection, SessionLocal
│   ├── webhook.py               # WhatsApp message processing
│   ├── ai_reply.py              # Claude AI integration
│   ├── email_helper.py          # All transactional emails (4 types)
│   ├── auth.py                  # Login, JWT tokens
│   ├── register.py              # 4-step registration flow
│   ├── payments.py              # Paystack webhook
│   └── subscription.py          # Renewal reminders, plan limits
│
├── django_admin/                # Django project root
│   ├── django_admin/            # Django settings, urls, celery config
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── celery.py            # Celery app configuration
│   │   └── __init__.py          # Celery auto-discovery
│   ├── core/                    # Django app
│   │   ├── models.py            # Django ORM models
│   │   ├── views.py             # Dashboard views with pagination
│   │   ├── admin.py             # Django admin customisation
│   │   ├── tasks.py             # Celery tasks + email template
│   │   ├── urls.py
│   │   └── templates/           # HTML templates
│   └── manage.py
│
└── venv/                        # Python virtual environment

6. Database Models
Client
Core model — one row per registered business. Stores Meta credentials, subscription details, plan, payment status, AI usage counters, and token validity flag.
AutoReplyRule
Keyword-triggered reply rules. Each rule has a trigger keyword, response text, and is_active flag. Ordered by priority for matching.
MessageLog
Every inbound and outbound WhatsApp message stored here. Includes direction, sender_number, timestamp, and whatsapp_message_id for deduplication.
Contact
Auto-saved customer contacts per client. Tracks opt-out status (STOP/START commands).
Product
Product catalogue entries with name, description, price, category, keyword, and Cloudinary image URL.
Broadcast
Bulk WhatsApp message campaigns with status tracking (pending → running → completed).
BusinessHours
Per-day open/close times for each client. Bot sends closed message outside configured hours.
MessageTemplate
Custom message overrides — welcome, menu, closed, handoff, fallback. Falls back to default if not set.
SubscriptionPlan
DB-driven pricing — Starter, Growth, Pro plans with price_kobo, description, and is_active flag. Editable from Django admin.
EmailCampaign
Bulk email campaigns with recipient_type (all/plan/selected), scheduling, status tracking, and per-batch progress.
CampaignLog
Per-client send log for each campaign — tracks sent, failed, opened status and error messages.
PasswordResetToken
Secure time-limited tokens for password reset flow.

7. Auto-Reply Message Logic
Every inbound message goes through the following priority chain:

    1. STOP / START — opt-out and opt-in handling (highest priority)
    2. Business Hours — closed message if outside configured hours
    3. New User — welcome message on first interaction
    4. menu keyword — full menu of categories and options
    5. human / agent keyword — handoff message + email alert to business owner
    6. Auto-reply rules — keyword match from DB rules (by priority)
    7. Category match — text matches a product category name
    8. Product keyword — exact product keyword match → shows product details
    9. AI Reply (Growth & Pro) — Claude AI with 529 retry logic
    10. Fallback — default or custom fallback message (lowest priority)

8. Subscription Plans
Plan	Price (Monthly)	AI Replies	Features
Starter	Set in Django Admin	None (rules only)	Rules, products, broadcasts
Growth	Set in Django Admin	Limited (monthly reset)	All Starter + AI replies
Pro	Set in Django Admin	Unlimited	All Growth + unlimited AI

Plan prices are managed entirely from the Django admin panel — no code changes needed to update pricing.

9. Email System
Transactional Emails (email_helper.py)
Four professional HTML emails with dark-mode-safe design:
    • Human Handoff Alert — sent to business owner when customer types 'human'
    • Password Reset — secure token link, expires in 1 hour
    • Registration Confirmation — sent on signup, shows pending activation status
    • Account Activation — sent when admin activates the client account

Email Campaign System (tasks.py + Celery)
    • Send to: all clients / by plan / selected clients
    • HTML body with {business_name}, {email}, {plan} placeholders auto-replaced
    • Professional WhatsApp-themed template wraps every campaign automatically
    • Batched sending: 50 emails per batch, 1.5 second pause (Gmail safe)
    • Real-time progress bar in Django admin refreshes per batch
    • Schedule campaigns for future dates — Celery Beat checks every 60 seconds
    • Resume-safe: won't re-send to already-sent clients if task restarts
    • Per-client CampaignLog tracks sent / failed / opened status

Email Provider
Current (development): Gmail SMTP — 500 emails/day limit
After hosting: Domain email — free with hosting, higher rate limits
At scale: SendGrid — same code, just update .env credentials

10. Running the Project Locally
Required Terminals
You need 5 things running simultaneously:

Terminal 1 — FastAPI (WhatsApp webhook):
cd ALX_project
uvicorn app.main:app --reload --port 8000

Terminal 2 — Django (Admin dashboard):
cd ALX_project/django_admin
python manage.py runserver 8001

Terminal 3 — Celery Worker:
cd ALX_project/django_admin
celery -A django_admin worker --loglevel=info --pool=solo

Terminal 4 — Celery Beat (scheduler):
cd ALX_project/django_admin
celery -A django_admin beat --loglevel=info

Terminal 5 (WSL) — Redis:
wsl
sudo service redis start
redis-cli ping   # should return PONG

Ngrok (separate window):
ngrok http 8000
# Copy the https URL → paste into Meta webhook settings

11. Environment Variables (.env)
# Database
DATABASE_URL=postgresql://user:password@localhost/botmart_db

# Meta / WhatsApp
VERIFY_TOKEN=your_webhook_verify_token

# Email (Gmail SMTP)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_FROM=your@gmail.com
MAIL_FROM_NAME=BotMart

# Support
SUPPORT_WHATSAPP=2348000000000
BASE_URL=http://localhost:8001

# Paystack
PAYSTACK_SECRET_KEY=sk_test_xxxxx
PAYSTACK_PUBLIC_KEY=pk_test_xxxxx

# Anthropic (Claude AI)
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Cloudinary (product images)
CLOUDINARY_CLOUD_NAME=your_cloud
CLOUDINARY_API_KEY=xxxxx
CLOUDINARY_API_SECRET=xxxxx

# Django
SECRET_KEY=your_django_secret_key
DEBUG=True

# Celery / Redis
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0

12. Known Issues & Fixes Applied
    • Meta webhook retry loops — fixed by returning 200 immediately and processing in BackgroundTasks
    • Duplicate message processing — fixed with whatsapp_message_id unique index
    • Claude 529 overload errors — fixed with 2-second retry logic before fallback
    • celery.py naming conflict — must be inside django_admin/ folder, not project root
    • Django initial migration on existing DB — fixed with python manage.py migrate --fake core 0001_initial
    • Redis on Windows — use WSL (sudo service redis start) or Memurai
    • Gmail dark mode in emails — fixed with color-scheme meta tag + [data-ogsc] CSS overrides + !important on all colours
    • f-string CSS brace conflict in email templates — fixed by using __PLACEHOLDER__ tokens with .replace()
    • SQLAlchemy duplicate model class — fixed by removing whatsapp_message_id from Client (was accidentally added there)

13. Pre-Deployment Checklist
    • Set DEBUG=False in Django settings
    • Set BASE_URL to production domain in .env
    • Switch email provider from Gmail to domain email or SendGrid
    • Set up Gunicorn for Django (replace runserver)
    • Configure Nginx as reverse proxy
    • Set up Redis as system service (not WSL)
    • Configure Celery worker + beat as systemd services
    • Set up SSL certificate (Let's Encrypt)
    • Update Meta webhook URL to production domain
    • Add ALLOWED_HOSTS in Django settings
    • Set up PostgreSQL backups
    • Set PAYSTACK_SECRET_KEY to live key (not test)
    • Test all 4 email types in production
    • Send test campaign to 1 client before full launch

BotMart — Built with FastAPI, Django, Celery & the Meta WhatsApp Business API
© 2026 BotMart  •  Lagos, Nigeria  •  Confidential