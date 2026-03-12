# BotMart — Complete Project Summary
**Date:** March 2026 | **Status:** Ready for Production Deployment

---

## 1. PROJECT OVERVIEW

BotMart is a multi-tenant WhatsApp Business automation SaaS platform built for Nigerian businesses. Clients register, pay via Paystack, connect their WhatsApp Business Account via Meta Cloud API, and get a fully automated WhatsApp bot — auto-replies, product catalogue, broadcasts, AI smart replies, and more.

**Architecture: Dual-App**
- **FastAPI** (port 8000) — handles all WhatsApp webhooks from Meta in real time
- **Django** (port 8001) — client-facing dashboard + Django admin for the owner

Both apps share the **same PostgreSQL database** and `.env` file.

---

## 2. FOLDER STRUCTURE

```
ALX_project/
│
├── fastapi_app/                        # FastAPI — webhook engine
│   ├── main.py                         # App entry, APScheduler, router registration
│   ├── .env                            # All shared environment variables
│   ├── app/
│   │   ├── models.py                   # SQLAlchemy models (mirrors Django models)
│   │   ├── database.py                 # PostgreSQL connection (SQLAlchemy)
│   │   ├── ai_reply.py                 # Claude AI smart reply logic
│   │   ├── subscription_checker.py     # Daily subscription expiry checker (APScheduler)
│   │   ├── cloudinary_helper.py        # Cloudinary image upload/delete
│   │   └── routers/
│   │       ├── webhook.py              # Main WhatsApp webhook handler
│   │       ├── payment.py              # Stub router (payments handled by Django)
│   │       └── __init__.py
│
├── django_admin/                       # Django — dashboard + admin
│   ├── manage.py
│   ├── django_admin/
│   │   ├── settings.py                 # Django settings
│   │   ├── urls.py                     # Root URL config
│   │   ├── celery.py                   # Celery app configuration
│   │   └── wsgi.py
│   └── core/
│       ├── models.py                   # Django ORM models
│       ├── views.py                    # All client-facing views (1500+ lines)
│       ├── admin.py                    # Django admin customisation
│       ├── urls.py                     # App URL patterns
│       ├── email_helper.py             # Email sending functions
│       ├── cloudinary_helper.py        # Cloudinary helpers
│       ├── tasks.py                    # Celery tasks (email campaigns)
│       └── templates/
│           ├── core/
│           │   ├── base.html           # Shared base with nav + footer
│           │   ├── index.html          # Public landing page
│           │   ├── login.html          # Client login
│           │   ├── register.html       # Registration (step 1/3)
│           │   ├── meta_setup.html     # WhatsApp credentials (step 2/3)
│           │   ├── subscribe.html      # Subscription/payment (step 3/3)
│           │   ├── pending.html        # Awaiting admin activation
│           │   ├── dashboard.html      # Main client dashboard
│           │   ├── profile.html        # Profile + token update + AI description + delete account
│           │   ├── rules.html          # Auto-reply rules management
│           │   ├── products.html       # Product catalogue management
│           │   ├── contacts.html       # WhatsApp contacts list
│           │   ├── broadcast.html      # Broadcast message sender
│           │   ├── analytics.html      # Message analytics + charts
│           │   ├── business_hours.html # Business hours per day
│           │   ├── message_history.html# Full message log
│           │   ├── message_templates.html # Welcome/menu/fallback messages
│           │   ├── renew.html          # Subscription renewal with duration tabs
│           │   ├── forgot_password.html
│           │   ├── reset_password.html
│           │   ├── privacy_policy.html # Privacy policy (BotMart design system)
│           │   ├── terms.html          # Terms & conditions (BotMart design system)
│           │   └── account_deleted.html
│           └── admin/
│               └── payment_log_changelist.html  # Custom payment analytics dashboard
│       └── static/
│           └── core/
│               └── css/
│                   └── botmart.css     # Full design system (tokens, nav, legal, auth)
```

---

## 3. DATABASE MODELS

### Django `core/models.py` + FastAPI `app/models.py` (shared tables)

| Model | Table | Key Fields |
|---|---|---|
| `Client` | `clients` | business_name, email, hashed_password, whatsapp_number, access_token, phone_number_id, waba_id, plan, payment_status, subscription_start, subscription_end, grace_period_end, subscription_months, is_active, token_valid, reminder_7_sent, reminder_3_sent, ai_replies_today, ai_replies_reset_date, business_description |
| `AutoReplyRule` | `auto_reply_rules` | client, trigger_keyword, response_text, is_active |
| `MessageLog` | `message_logs` | client, sender_number, message_text, direction, timestamp |
| `Contact` | `contacts` | client, phone_number, name, opted_out, last_message_at |
| `Broadcast` | `broadcasts` | client, message, status, sent_count, failed_count, scheduled_at |
| `BusinessHours` | `business_hours` | client, day_of_week (0–6), open_time, close_time, is_open |
| `Product` | `products` | client, name, description, price, keyword, category, image_url, image_public_id, is_active |
| `MessageTemplate` | `message_templates` | client, welcome_message, menu_message, closed_message, handoff_message, fallback_message |
| `PasswordResetToken` | `password_reset_tokens` | client, token, expires_at, used |
| `SubscriptionPlan` | `subscription_plans` | name, display_name, price_naira, price_kobo, discount_3_months, discount_6_months, discount_12_months, is_active |
| `PaymentLog` | `payment_logs` | client, reference, amount_kobo, plan, months, is_renewal, subscription_start, subscription_end, paid_at |
| `EmailCampaign` | `email_campaigns` | subject, body, recipient_type, target_plan, selected_clients, status, scheduled_at, sent_count, failed_count |
| `CampaignLog` | `campaign_logs` | campaign, client, email, status, sent_at, opened_at, error_msg |

---

## 4. ALL URL ROUTES (Django — port 8001)

### Public routes (no login required)
```python
/                           # Landing page
/login/                     # Client login
/register/                  # Registration step 1
/meta-setup/                # Registration step 2 — WhatsApp credentials
/subscribe/                 # Registration step 3 — plan + payment
/payment/verify/            # Paystack callback after new subscription
/payment/renew-verify/      # Paystack callback after renewal
/pending/                   # Awaiting admin activation
/paystack/webhook/          # Paystack webhook (csrf_exempt + HMAC verified)
/forgot-password/           # Password reset request
/reset-password/<token>/    # Password reset form
/privacy/                   # Privacy policy
/terms/                     # Terms & conditions
/account-deleted/           # Post-deletion confirmation page
```

### Protected routes (@client_required)
```python
/dashboard/                 # Main dashboard
/profile/                   # Profile, token, AI description
/profile/update-token/      # Update Meta access token
/profile/test-connection/   # Test Meta API connection (AJAX)
/profile/ai-description/    # Update AI business description
/delete-account/            # Delete account + all data
/rules/                     # Auto-reply rules CRUD
/products/                  # Product catalogue CRUD + Cloudinary images
/contacts/                  # Contact list + CSV import + opt-out management
/broadcast/                 # Broadcast message sender
/analytics/                 # Message analytics
/business-hours/            # Business hours per day of week
/message-history/           # Full paginated message log
/message-templates/         # Welcome/menu/fallback/handoff templates
/renew/                     # Subscription renewal (multi-month tabs)
```

### Django Admin (owner only — /admin/)
```python
/admin/core/client/             # All clients with inline rules, hours, payment history
/admin/core/paymentlog/         # Payment analytics dashboard (charts + stats)
/admin/core/autorreplyrule/
/admin/core/messagelog/
/admin/core/product/
/admin/core/messagetemplate/
/admin/core/passwordresettoken/
/admin/core/subscriptionplan/   # Manage plan prices + discounts
/admin/core/emailcampaign/      # Email campaigns with send action
/admin/core/campaignlog/
```

### FastAPI (port 8000)
```python
GET  /webhook/              # Meta webhook verification
POST /webhook/              # Incoming WhatsApp messages
GET  /test-subscription-check/  # Manually trigger subscription checker
```

---

## 5. COMPLETE FEATURE LIST

### Registration & Onboarding (3-step flow)
- Step 1: Account details (business name, email, password, WhatsApp number)
- Step 2: Meta credentials (access token validated live against Meta Graph API)
- Step 3: Plan selection + Paystack payment (multi-month with discounts)
- Pending page after payment awaiting admin activation
- Admin activates → client gets activation email → can log in

### Authentication & Security
- Bcrypt password hashing (passlib)
- Session-based auth with `client_required` decorator
- Subscription check on every protected page — redirects unpaid users to `/subscribe/`, expired users to `/renew/`
- Exempt routes: renew, payment_verify, renew_verify, paystack_webhook, logout
- Forgot password + reset password flow (token-based, 1-hour expiry)
- Delete account with password confirmation + "DELETE" typed confirmation
  - Deletes: messages, rules, contacts, broadcasts, business hours, products (+ Cloudinary images), templates, reset tokens, payment logs, client record

### Subscription System
- Plans: Starter (₦8,000/mo), Growth (₦18,000/mo), Pro (₦35,000/mo)
- Prices managed from Django admin (SubscriptionPlan model)
- Multi-month durations: 1 / 3 / 6 / 12 months with % discounts
- Paystack payment integration (hosted checkout)
- Payment verified via:
  1. `paystack_webhook` (HMAC-verified, csrf_exempt) — fires immediately
  2. `payment_verify` / `renew_verify` — browser redirect fallback
- Duplicate payment guard — PaymentLog checked by reference before processing
- `is_renewal` string→boolean fix for Paystack metadata
- Grace period: 7 days after expiry before bot pauses
- Subscription checker (APScheduler, runs daily at 8am):
  - 7-day reminder email
  - 3-day urgent reminder email
  - Expiry day: sets `payment_status = expired`, sends bot-paused email
  - After grace period: sets `is_active = False`

### WhatsApp Bot (FastAPI webhook)
Message processing priority chain:
1. STOP/START — opt-out / opt-in
2. Business hours check — closed message if outside hours
3. New contact — welcome message
4. "menu" keyword — menu message
5. "human"/"agent" keyword — handoff message
6. Auto-reply rules (substring match, case-insensitive)
7. Product category keyword
8. Individual product keyword
9. AI smart reply (Growth/Pro only)
10. Fallback message

Webhook deduplication — prevents Meta retry loops (message ID tracked)
Claude 529 retry logic — retries AI calls up to 3× with backoff

### AI Smart Replies
- Starter: blocked
- Growth: 100 AI replies/day (counter resets daily)
- Pro: unlimited
- System prompt built from: business_description + all products (name/price/keyword/category) + all auto-reply rules
- Model: `claude-haiku-4-5-20251001` (fast + cheap for WhatsApp)
- max_tokens: 300
- Falls through to fallback if blocked/error
- Business description editable from profile page (max 2000 chars)

### Plan Limits Enforced
| Feature | Starter | Growth | Pro |
|---|---|---|---|
| Auto-reply rules | 10 max | Unlimited | Unlimited |
| Products | 10 max | Unlimited | Unlimited |
| Contacts | 500 max | Unlimited | Unlimited |
| AI replies/day | 0 | 100 | Unlimited |
| Broadcasts | ❌ | ✅ | ✅ |

### Dashboard Features
- Total contacts, messages sent today, active rules, products count
- WhatsApp connection status
- Recent message log
- Days remaining on subscription

### Analytics
- Messages sent over time (line chart)
- Messages by day of week (bar chart)
- Top triggered keywords

### Products & Catalogue
- CRUD with Cloudinary image upload
- Category grouping
- Keyword-based auto-response in bot

### Contacts
- Auto-created when new WhatsApp number messages
- CSV import
- Opt-out management (STOP/START commands)
- Pagination

### Broadcasts
- Send to all active contacts or selected
- Scheduled broadcasts
- Sent/failed count tracking
- Growth + Pro only (blocked on Starter)

### Business Hours
- Per day of week (Mon–Sun)
- Open/close time
- is_open toggle per day
- Overnight hours supported (e.g. 10pm–2am)
- Bot sends closed message outside hours

### Message Templates
- Welcome message (first-time contact)
- Menu message ("menu" keyword)
- Closed message (outside hours)
- Handoff message ("human" keyword)
- Fallback message (no match)
- Auto-generates smart suggestions based on client's rules and products

### Email Campaigns (Owner tool — admin only)
- Send email to: all clients / by plan / selected clients
- Scheduled campaigns
- Celery + Redis background processing
- Progress tracking (sent/failed count)
- Campaign log per recipient

### Payment Analytics Dashboard
- Total revenue (all time + this month)
- Month-over-month growth %
- New vs renewal breakdown
- Revenue by plan (doughnut chart)
- Monthly revenue trend (line chart, last 6 months)
- Duration breakdown table
- Recent 10 payments
- Charts via Chart.js 4.4.0

### Legal Pages
- Privacy Policy (12 sections, BotMart design system)
- Terms & Conditions (12 sections, BotMart design system)
- Both: sticky sidebar TOC on desktop, collapsible tap-to-expand on mobile
- Consent checkboxes on registration (Terms + WhatsApp Business Policy)
- Server-side validation of consent before account creation

---

## 6. ENVIRONMENT VARIABLES (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/botmart_db

# Meta / WhatsApp
VERIFY_TOKEN=your_webhook_verify_token

# Paystack
PAYSTACK_SECRET_KEY=sk_live_...

# Django
BASE_URL=https://your-domain.com
DJANGO_SECRET_KEY=your_secret_key
ALLOWED_HOSTS=localhost,127.0.0.1,.ngrok-free.app,your-domain.com
DEBUG=False

# Anthropic
CLAUDE_API_KEY=sk-ant-...

# Cloudinary
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...

# Email (Gmail SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=BotMart <your@gmail.com>

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0

# App
APP_NAME=BotMart
```

---

## 7. SERVICES REQUIRED FOR PRODUCTION

| Service | Purpose |
|---|---|
| PostgreSQL | Shared database |
| Redis | Celery broker for email campaigns |
| Celery Worker | Background email campaign sending |
| APScheduler | Subscription expiry checks (inside FastAPI) |
| Cloudinary | Product image storage |
| Paystack | Payment processing |
| Meta WhatsApp Business API | WhatsApp message sending/receiving |
| Anthropic API | AI smart replies |
| SMTP (Gmail/SendGrid) | Transactional emails |

---

## 8. KNOWN FIXES APPLIED (Important for going live)

1. **`@csrf_exempt`** on `paystack_webhook` — required for Paystack server-to-server POST
2. **HMAC signature verification** on webhook — security replacement for CSRF
3. **`is_renewal` string→bool fix** — Paystack sends `"true"` as string, not Python `True`
4. **Session restore** in `payment_verify` + `renew_verify` — Paystack breaks browser session during redirect, session must be rebuilt from metadata `client_id`
5. **Duplicate payment guard** — checks `PaymentLog.objects.filter(reference=reference).exists()` before processing
6. **`ALLOWED_HOSTS`** — includes `.ngrok-free.app` wildcard for development
7. **`format_html` fix** — Django 6 requires at least one `{}` argument; static HTML badges use `mark_safe` instead
8. **`client_required` exempt list** — renew/verify/webhook pages are always accessible so payment flow can't be blocked

---

## 9. DEPLOYMENT CHECKLIST

- [ ] Set `DEBUG=False` in settings.py
- [ ] Set `ALLOWED_HOSTS` to your real domain
- [ ] Run `python manage.py collectstatic`
- [ ] Run `python manage.py migrate`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Create SubscriptionPlan records in Django admin (starter/growth/pro)
- [ ] Set Paystack webhook URL to `https://yourdomain.com/paystack/webhook/`
- [ ] Set Meta webhook URL to `https://yourdomain.com/webhook/` (port 8000)
- [ ] Start Celery: `celery -A django_admin worker --loglevel=info`
- [ ] Start FastAPI: `uvicorn main:app --host 0.0.0.0 --port 8000`
- [ ] Start Django: `gunicorn django_admin.wsgi --bind 0.0.0.0:8001`
- [ ] Ensure Redis is running for Celery
- [ ] Test a complete registration + payment flow end-to-end
- [ ] Test a WhatsApp message to confirm webhook is live

---

## 10. KICK-OFF PROMPT FOR NEW CHAT

Copy and paste this exactly into your new chat:

---

> I am continuing development of **BotMart** — a multi-tenant WhatsApp Business automation SaaS platform for Nigerian businesses. The project is nearly complete and ready for production.
>
> **Architecture:**
> - **FastAPI** (port 8000) — WhatsApp webhook handler, AI replies, subscription checker
> - **Django** (port 8001) — client dashboard, admin panel, payment processing
> - Both share one **PostgreSQL** database and one `.env` file
>
> **Tech stack:** FastAPI, Django 6, PostgreSQL, SQLAlchemy, Celery + Redis, Paystack (payments), Meta WhatsApp Cloud API, Anthropic Claude Haiku (AI replies), Cloudinary (images), Gmail SMTP
>
> **What is fully built:**
> - 3-step registration flow (account → Meta credentials → Paystack payment)
> - Subscription system: Starter/Growth/Pro plans, multi-month discounts (3/6/12 months), grace period, Paystack webhook (HMAC verified, csrf_exempt), payment_verify + renew_verify with session restore, duplicate payment guard
> - WhatsApp bot: auto-replies, product catalogue, business hours, opt-out/in, menu system, AI smart replies (Claude Haiku, Growth/Pro only with daily limits), fallback chain
> - Client dashboard: rules, products (Cloudinary), contacts, broadcasts, analytics, business hours, message templates, message history — all paginated
> - Profile: token management, AI description, delete account (with password + "DELETE" confirmation)
> - Django admin: client management, payment analytics dashboard (Chart.js), email campaign system (Celery), subscription plan price management
> - Auth: bcrypt passwords, session auth, `client_required` decorator with subscription check, forgot/reset password, consent checkboxes on registration
> - Legal: Privacy Policy + Terms & Conditions pages (BotMart design system, mobile responsive with collapsible TOC)
> - Design system: `botmart.css` with CSS tokens, Syne + DM Sans fonts, auth layout, legal layout, page hero, nav, footer
> - Subscription checker: APScheduler runs daily — 7-day reminder, 3-day reminder, expiry pause, grace period deactivation
>
> **Key bugs already fixed:**
> - `@csrf_exempt` + HMAC on Paystack webhook
> - `is_renewal` string→bool conversion
> - Session restore in verify views after Paystack redirect
> - `format_html` → `mark_safe` for static HTML in Django 6 admin
> - `client_required` exempt list for payment flow
> - `ALLOWED_HOSTS` wildcard for ngrok
>
> **I am ready to go live. Please help me with [YOUR NEXT TASK HERE].**

---

*Replace `[YOUR NEXT TASK HERE]` with what you need — e.g. "deploying to a VPS/Railway", "setting up a custom domain with nginx", "adding a support contact page", "final UI polish on the landing page", etc.*
