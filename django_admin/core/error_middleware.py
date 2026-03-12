# core/error_middleware.py
# ─────────────────────────────────────────────────────────────────
# Middleware that catches every unhandled exception, saves it to
# the ErrorLog table, and emails the admin.
#
# SETUP:
#   1. Add 'core.error_middleware.ErrorTrackingMiddleware' to
#      MIDDLEWARE in settings.py — put it FIRST in the list.
#   2. Add ADMIN_NOTIFY_EMAIL to your .env
#   3. Run: python manage.py makemigrations && python manage.py migrate
# ─────────────────────────────────────────────────────────────────

import traceback
import logging
from django.http import HttpResponse
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class ErrorTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as exception:
            try:
                self._save_and_notify(request, exception)
            except Exception as e:
                logger.error(f"ErrorTrackingMiddleware failed: {e}")
            raise  # re-raise so Django still shows the debug page locally

    def process_exception(self, request, exception):
        """Called automatically by Django for every unhandled exception."""
        try:
            self._save_and_notify(request, exception)
        except Exception as e:
            # Never let error tracking itself crash the app
            logger.error(f"ErrorTrackingMiddleware failed: {e}")
        return None  # let Django's normal error handling continue

    def _save_and_notify(self, request, exception):
        from .models import ErrorLog, Client

        tb    = traceback.format_exc()
        etype = type(exception).__name__
        msg   = str(exception)
        path  = request.path
        method = request.method

        # Try to identify which client triggered this
        client       = None
        client_email = ''
        try:
            client_id = request.session.get('client_id')
            if client_id:
                client = Client.objects.get(id=client_id)
                client_email = client.email
        except Exception:
            pass

        # Save to database
        error_entry = ErrorLog.objects.create(
            level          = 'critical' if isinstance(exception, (SystemExit, MemoryError)) else 'error',
            path           = path[:500],
            method         = method,
            client         = client,
            client_email   = client_email,
            exception_type = etype,
            message        = msg[:5000],
            traceback      = tb[:10000],
            user_agent     = request.META.get('HTTP_USER_AGENT', '')[:500],
        )

        # Email admin
        self._send_alert_email(error_entry, request, tb)

    def _send_alert_email(self, error_entry, request, tb):
        admin_email = getattr(settings, 'ADMIN_NOTIFY_EMAIL', None)
        if not admin_email:
            return

        subject = f"[BotMart Error] {error_entry.exception_type} on {error_entry.path}"

        body = f"""
BotMart — Unhandled Exception Alert
{'=' * 50}

Type      : {error_entry.exception_type}
Message   : {error_entry.message}
URL       : {error_entry.method} {error_entry.path}
Client    : {error_entry.client_email or 'Not logged in'}
Time      : {error_entry.occurred_at:%d %b %Y at %H:%M:%S}
Error ID  : #{error_entry.id}

TRACEBACK:
{'─' * 50}
{tb}

{'─' * 50}
View in admin: {getattr(settings, 'BASE_URL', 'http://localhost:8001')}/admin/core/errorlog/{error_entry.id}/change/
"""

        try:
            send_mail(
                subject      = subject,
                message      = body,
                from_email   = settings.EMAIL_HOST_USER,
                recipient_list = [admin_email],
                fail_silently = True,
            )
        except Exception as e:
            logger.error(f"Failed to send error alert email: {e}")