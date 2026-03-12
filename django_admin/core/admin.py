from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth, TruncDate
from datetime import date, timedelta
import json

from passlib.context import CryptContext

from .models import (
    Client, AutoReplyRule, MessageLog, BusinessHours,
    Product, MessageTemplate, PasswordResetToken,
    SubscriptionPlan, EmailCampaign, CampaignLog, PaymentLog
)
from .email_helper import send_activation_email

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ─────────────────────────────────────────────
# CLIENT ADMIN
# ─────────────────────────────────────────────

class AutoReplyRuleInline(admin.TabularInline):
    model    = AutoReplyRule
    extra    = 1
    fields   = ['trigger_keyword', 'response_text', 'is_active']
    can_delete = True
    verbose_name = "Auto Reply Rule"
    verbose_name_plural = "Auto Reply Rules"


class BusinessHoursInline(admin.TabularInline):
    model      = BusinessHours
    extra      = 0
    fields     = ['day_of_week', 'open_time', 'close_time', 'is_open']
    ordering   = ['day_of_week']
    can_delete = False
    verbose_name = "Business Hour"
    verbose_name_plural = "Business Hours"


class PaymentLogInline(admin.TabularInline):
    model           = PaymentLog
    extra           = 0
    can_delete      = False
    readonly_fields = [
        'reference', 'amount_naira_display', 'plan',
        'months', 'is_renewal', 'subscription_start',
        'subscription_end', 'paid_at'
    ]
    fields = [
        'reference', 'amount_naira_display', 'plan',
        'months', 'is_renewal', 'subscription_start',
        'subscription_end', 'paid_at'
    ]
    verbose_name = "Payment"
    verbose_name_plural = "Payment History"

    def amount_naira_display(self, obj):
        return f"₦{obj.amount_naira:,}"
    amount_naira_display.short_description = 'Amount'

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = [
        'business_name', 'email', 'plan',
        'payment_status', 'subscription_duration',
        'days_remaining', 'token_status',
        'rule_count', 'created_at'
    ]
    list_filter  = ['is_active', 'token_valid', 'payment_status', 'plan']
    search_fields = ['business_name', 'email']
    inlines      = [AutoReplyRuleInline, BusinessHoursInline, PaymentLogInline]
    exclude      = ['hashed_password']
    readonly_fields = ['created_at']
    actions      = ['activate_clients']

    def rule_count(self, obj):
        return obj.rules.count()
    rule_count.short_description = 'Rules'

    def token_status(self, obj):
        return "✅ Valid" if obj.token_valid else "❌ Invalid"
    token_status.short_description = 'Token'

    def subscription_duration(self, obj):
        months = getattr(obj, 'subscription_months', 1) or 1
        label  = {1: '1 mo', 3: '3 mos', 6: '6 mos', 12: '12 mos'}.get(months, f'{months} mos')
        return label
    subscription_duration.short_description = 'Duration'

    def days_remaining(self, obj):
        if not obj.subscription_end:
            return "—"
        days = (obj.subscription_end - date.today()).days
        if days < 0:
            return format_html(
                '<span style="color:#dc3545;font-weight:600;">❌ Expired {}d ago</span>',
                abs(days)
            )
        elif days <= 3:
            return format_html(
                '<span style="color:#dc3545;font-weight:600;">🔴 {}d left</span>', days
            )
        elif days <= 7:
            return format_html(
                '<span style="color:#f59e0b;font-weight:600;">🟡 {}d left</span>', days
            )
        return format_html(
            '<span style="color:#059669;font-weight:600;">🟢 {}d left</span>', days
        )
    days_remaining.short_description = 'Subscription'

    def activate_clients(self, request, queryset):
        activated = 0
        for client in queryset:
            if not client.is_active:
                client.is_active = True
                client.save()
                send_activation_email(client.email, client.business_name)
                activated += 1
        self.message_user(
            request,
            f"✅ {activated} client(s) activated and notified by email."
        )
    activate_clients.short_description = "✅ Activate selected clients and notify by email"


# ─────────────────────────────────────────────
# PAYMENT LOG ADMIN
# ─────────────────────────────────────────────

@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    change_list_template = 'admin/payment_log_changelist.html'

    list_display = [
        'paid_at_display', 'client_name', 'plan_badge',
        'duration_badge', 'amount_display',
        'type_badge', 'subscription_end'
    ]
    list_filter  = ['plan', 'months', 'is_renewal',
                    ('paid_at', admin.DateFieldListFilter)]
    search_fields = ['client__business_name', 'client__email', 'reference']
    readonly_fields = [
        'client', 'reference', 'amount_kobo', 'plan',
        'months', 'is_renewal', 'subscription_start',
        'subscription_end', 'paid_at'
    ]
    ordering = ['-paid_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def paid_at_display(self, obj):
        return obj.paid_at.strftime('%d %b %Y, %I:%M %p')
    paid_at_display.short_description = 'Date'
    paid_at_display.admin_order_field = 'paid_at'

    def client_name(self, obj):
        return format_html(
            '<strong>{}</strong><br/>'
            '<small style="color:#9ca3af;">{}</small>',
            obj.client.business_name,
            obj.client.email
        )
    client_name.short_description = 'Client'

    def amount_display(self, obj):
        return format_html(
            '<span style="font-weight:700;color:#065f46;font-size:1rem;">₦{}</span>',
            f"{obj.amount_naira:,}"
        )
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount_kobo'

    def plan_badge(self, obj):
        colors = {
            'starter': '#6b7280',
            'growth':  '#2563eb',
            'pro':     '#7c3aed',
        }
        color = colors.get(obj.plan, '#6b7280')
        return format_html(
            '<span style="background:{};color:white;padding:2px 10px;'
            'border-radius:20px;font-size:0.78rem;font-weight:600;">{}</span>',
            color, obj.plan.title()
        )
    plan_badge.short_description = 'Plan'

    def duration_badge(self, obj):
        label = {1: '1 Month', 3: '3 Months', 6: '6 Months', 12: '12 Months'}.get(
            obj.months, f'{obj.months} Months'
        )
        bg = '#f3f4f6'
        color = '#374151'
        if obj.months >= 12:
            bg, color = '#fef9c3', '#854d0e'
        elif obj.months >= 6:
            bg, color = '#dcfce7', '#166534'
        elif obj.months >= 3:
            bg, color = '#dbeafe', '#1e40af'
        return format_html(
            '<span style="background:{};color:{};padding:2px 10px;'
            'border-radius:20px;font-size:0.78rem;font-weight:600;">{}</span>',
            bg, color, label
        )
    duration_badge.short_description = 'Duration'

    def type_badge(self, obj):
        from django.utils.safestring import mark_safe
        if obj.is_renewal:
            return mark_safe(
                '<span style="background:#fef3c7;color:#92400e;padding:2px 8px;'
                'border-radius:20px;font-size:0.75rem;font-weight:600;">🔄 Renewal</span>'
            )
        return mark_safe(
            '<span style="background:#d1fae5;color:#065f46;padding:2px 8px;'
            'border-radius:20px;font-size:0.75rem;font-weight:600;">✨ New</span>'
        )
    type_badge.short_description = 'Type'

    def changelist_view(self, request, extra_context=None):
        """Inject analytics data into the changelist template."""
        extra_context = extra_context or {}

        # ── Totals ──
        all_payments  = PaymentLog.objects.all()
        total_revenue = all_payments.aggregate(t=Sum('amount_kobo'))['t'] or 0
        total_count   = all_payments.count()

        today        = date.today()
        month_start  = today.replace(day=1)
        this_month   = all_payments.filter(paid_at__date__gte=month_start)
        month_revenue = this_month.aggregate(t=Sum('amount_kobo'))['t'] or 0
        month_count   = this_month.count()

        last_month_start = (month_start - timedelta(days=1)).replace(day=1)
        last_month_end   = month_start - timedelta(days=1)
        last_month_rev   = all_payments.filter(
            paid_at__date__gte=last_month_start,
            paid_at__date__lte=last_month_end
        ).aggregate(t=Sum('amount_kobo'))['t'] or 0

        # ── MoM growth ──
        if last_month_rev > 0:
            mom_growth = round(((month_revenue - last_month_rev) / last_month_rev) * 100, 1)
        else:
            mom_growth = 100.0 if month_revenue > 0 else 0.0

        # ── New vs Renewal ──
        new_count     = all_payments.filter(is_renewal=False).count()
        renewal_count = all_payments.filter(is_renewal=True).count()

        # ── Plan breakdown ──
        plan_data = all_payments.values('plan').annotate(
            revenue=Sum('amount_kobo'),
            count=Count('id')
        ).order_by('-revenue')

        # ── Duration breakdown ──
        duration_data = all_payments.values('months').annotate(
            count=Count('id'),
            revenue=Sum('amount_kobo')
        ).order_by('months')

        # ── Monthly trend (last 6 months) ──
        six_months_ago = today - timedelta(days=180)
        monthly_trend  = (
            all_payments
            .filter(paid_at__date__gte=six_months_ago)
            .annotate(month=TruncMonth('paid_at'))
            .values('month')
            .annotate(revenue=Sum('amount_kobo'), count=Count('id'))
            .order_by('month')
        )

        trend_labels  = [r['month'].strftime('%b %Y') for r in monthly_trend]
        trend_revenue = [r['revenue'] // 100 for r in monthly_trend]
        trend_counts  = [r['count'] for r in monthly_trend]

        # ── Recent payments ──
        recent = all_payments.select_related('client')[:10]

        extra_context.update({
            'total_revenue':  total_revenue // 100,
            'total_count':    total_count,
            'month_revenue':  month_revenue // 100,
            'month_count':    month_count,
            'mom_growth':     mom_growth,
            'new_count':      new_count,
            'renewal_count':  renewal_count,
            'plan_data':      [
                {
                    'plan':    p['plan'].title(),
                    'revenue': p['revenue'] // 100,
                    'count':   p['count']
                }
                for p in plan_data
            ],
            'duration_data':  [
                {
                    'months':  d['months'],
                    'label':   {1:'1 Month',3:'3 Months',6:'6 Months',12:'12 Months'}.get(d['months'], f"{d['months']}mo"),
                    'count':   d['count'],
                    'revenue': d['revenue'] // 100,
                }
                for d in duration_data
            ],
            'trend_labels':   json.dumps(trend_labels),
            'trend_revenue':  json.dumps(trend_revenue),
            'trend_counts':   json.dumps(trend_counts),
            'recent':         recent,
        })

        return super().changelist_view(request, extra_context=extra_context)


# ─────────────────────────────────────────────
# MESSAGE LOG ADMIN
# ─────────────────────────────────────────────

@admin.register(MessageLog)
class MessageLogAdmin(admin.ModelAdmin):
    list_display  = ['client', 'sender_number', 'message_text', 'direction', 'timestamp']
    list_filter   = ['direction', 'client']
    search_fields = ['sender_number', 'message_text']
    readonly_fields = ['client', 'sender_number', 'message_text', 'direction', 'timestamp']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ─────────────────────────────────────────────
# PRODUCT ADMIN
# ─────────────────────────────────────────────

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ['name', 'client', 'keyword', 'price', 'category', 'is_active', 'created_at']
    list_filter   = ['is_active', 'client', 'category']
    search_fields = ['name', 'keyword', 'client__business_name']
    readonly_fields = ['created_at', 'image_url', 'image_public_id']


# ─────────────────────────────────────────────
# MESSAGE TEMPLATE ADMIN
# ─────────────────────────────────────────────

@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display  = ['client', 'has_welcome', 'has_menu', 'has_closed', 'has_handoff', 'has_fallback', 'updated_at']
    search_fields = ['client__business_name']
    readonly_fields = ['updated_at']

    def get_queryset(self, request):
        for client in Client.objects.all():
            MessageTemplate.objects.get_or_create(client=client)
        return super().get_queryset(request)

    def has_welcome(self, obj):  return "✔" if obj.welcome_message else "✘"
    has_welcome.short_description = 'Welcome'

    def has_menu(self, obj):     return "✔" if obj.menu_message else "✘"
    has_menu.short_description = 'Menu'

    def has_closed(self, obj):   return "✔" if obj.closed_message else "✘"
    has_closed.short_description = 'Closed'

    def has_handoff(self, obj):  return "✔" if obj.handoff_message else "✘"
    has_handoff.short_description = 'Handoff'

    def has_fallback(self, obj): return "✔" if obj.fallback_message else "✘"
    has_fallback.short_description = 'Fallback'


# ─────────────────────────────────────────────
# PASSWORD RESET TOKEN ADMIN
# ─────────────────────────────────────────────

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display  = ['client', 'token_short', 'expires_at', 'used', 'created_at']
    list_filter   = ['used', 'client']
    readonly_fields = ['client', 'token', 'expires_at', 'used', 'created_at']

    def token_short(self, obj):
        return f"{obj.token[:15]}..."
    token_short.short_description = 'Token'

    def has_add_permission(self, request):
        return False


# ─────────────────────────────────────────────
# SUBSCRIPTION PLAN ADMIN
# ─────────────────────────────────────────────

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display  = [
        'display_name', 'price_naira_display',
        'discounts_display', 'is_active', 'updated_at'
    ]
    list_editable = ['is_active']
    fields        = [
        'name', 'display_name', 'price_naira', 'description',
        'discount_3_months', 'discount_6_months', 'discount_12_months',
        'is_active'
    ]
    readonly_fields = ['created_at', 'updated_at']

    def price_naira_display(self, obj):
        return f"₦{obj.price_naira:,}"
    price_naira_display.short_description = 'Monthly Price'

    def discounts_display(self, obj):
        return format_html(
            '<small>'
            '3mo: <strong>{}%</strong> &nbsp;'
            '6mo: <strong>{}%</strong> &nbsp;'
            '12mo: <strong>{}%</strong>'
            '</small>',
            obj.discount_3_months,
            obj.discount_6_months,
            obj.discount_12_months,
        )
    discounts_display.short_description = 'Discounts'


# ─────────────────────────────────────────────
# EMAIL CAMPAIGN ADMIN
# ─────────────────────────────────────────────

class CampaignLogInline(admin.TabularInline):
    model           = CampaignLog
    extra           = 0
    readonly_fields = ['client', 'email', 'status', 'sent_at', 'opened_at', 'error_msg']
    can_delete      = False
    max_num         = 0
    show_change_link = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(EmailCampaign)
class EmailCampaignAdmin(admin.ModelAdmin):
    list_display  = [
        'subject', 'recipient_type', 'target_plan',
        'status_badge', 'progress_bar',
        'total_recipients', 'sent_count', 'failed_count',
        'scheduled_at', 'created_at'
    ]
    list_filter   = ['status', 'recipient_type', 'target_plan']
    search_fields = ['subject']
    readonly_fields = [
        'status', 'total_recipients', 'sent_count',
        'failed_count', 'created_at', 'updated_at', 'progress_display'
    ]
    fieldsets = (
        ('✉️ Email Content', {
            'fields': ('subject', 'body'),
        }),
        ('👥 Recipients', {
            'fields': ('recipient_type', 'target_plan', 'selected_clients'),
        }),
        ('⏰ Scheduling', {
            'fields': ('scheduled_at',),
        }),
        ('📊 Status & Progress', {
            'fields': (
                'status', 'total_recipients',
                'sent_count', 'failed_count',
                'progress_display', 'created_at', 'updated_at'
            ),
        }),
    )
    filter_horizontal = ['selected_clients']
    inlines           = [CampaignLogInline]
    actions           = ['action_send_now', 'action_queue_campaign']

    def status_badge(self, obj):
        colors = {
            'draft':     '#6c757d', 'queued':    '#fd7e14',
            'sending':   '#0d6efd', 'completed': '#198754', 'failed': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;'
            'border-radius:20px;font-size:0.8rem;font-weight:600;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def progress_bar(self, obj):
        pct   = obj.progress_percent
        color = '#198754' if pct == 100 else '#0d6efd'
        return format_html(
            '<div style="width:120px;background:#e9ecef;border-radius:4px;height:16px;">'
            '<div style="width:{}%;background:{};height:100%;border-radius:4px;"></div>'
            '</div><small style="color:#666;">{}%</small>',
            pct, color, pct
        )
    progress_bar.short_description = 'Progress'

    def progress_display(self, obj):
        pct = obj.progress_percent
        return format_html(
            '<div style="width:300px;background:#e9ecef;border-radius:6px;height:24px;">'
            '<div style="width:{}%;background:#198754;height:100%;border-radius:6px;"></div>'
            '</div>'
            '<p style="margin:4px 0 0;color:#666;">{} sent · {} failed · {}% complete</p>',
            pct, obj.sent_count, obj.failed_count, pct
        )
    progress_display.short_description = 'Progress'

    @admin.action(description='📤 Send now (immediately)')
    def action_send_now(self, request, queryset):
        from core.tasks import send_campaign
        count = 0
        for campaign in queryset.filter(status__in=['draft', 'queued']):
            campaign.status       = 'queued'
            campaign.scheduled_at = None
            campaign.save(update_fields=['status', 'scheduled_at'])
            send_campaign.delay(campaign.id)
            count += 1
        self.message_user(request, f"✅ {count} campaign(s) queued and sending.")

    @admin.action(description='📋 Mark as queued (will send at scheduled time)')
    def action_queue_campaign(self, request, queryset):
        count = queryset.filter(status='draft').update(status='queued')
        self.message_user(request, f"✅ {count} campaign(s) marked as queued.")


@admin.register(CampaignLog)
class CampaignLogAdmin(admin.ModelAdmin):
    list_display  = ['campaign', 'email', 'status', 'sent_at', 'opened_at']
    list_filter   = ['status', 'campaign']
    search_fields = ['email', 'campaign__subject']
    readonly_fields = ['campaign', 'client', 'email', 'status', 'sent_at', 'opened_at', 'error_msg']

    def has_add_permission(self, request):    return False
    def has_change_permission(self, request, obj=None): return False

# ── Paste this into core/admin.py ──
# (add to your existing admin.py, don't replace it)

from .models import ErrorLog

@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display  = (
        'occurred_at', 'level', 'exception_type',
        'short_message', 'path', 'client_email', 'resolved'
    )
    list_filter   = ('level', 'resolved', 'exception_type')
    search_fields = ('exception_type', 'message', 'path', 'client_email')
    readonly_fields = (
        'occurred_at', 'level', 'path', 'method',
        'client', 'client_email', 'exception_type',
        'message', 'traceback', 'user_agent',
    )
    list_per_page = 50
    ordering      = ('-occurred_at',)

    # Editable inline — admin can tick resolved and add notes
    fields = (
        'occurred_at', 'level', 'exception_type', 'message',
        'path', 'method', 'client', 'client_email',
        'user_agent', 'traceback',
        'resolved', 'notes',
    )

    def short_message(self, obj):
        return obj.message[:80] + '…' if len(obj.message) > 80 else obj.message
    short_message.short_description = 'Message'

    def has_add_permission(self, request):
        return False   # errors are only created by the system

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client')