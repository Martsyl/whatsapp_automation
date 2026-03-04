from django.contrib import admin
from .models import Client, AutoReplyRule, MessageLog, BusinessHours, Product, MessageTemplate, PasswordResetToken
from .email_helper import send_activation_email
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AutoReplyRuleInline(admin.TabularInline):
    model = AutoReplyRule
    extra = 1
    fields = ['trigger_keyword', 'response_text', 'is_active']
    can_delete = True
    verbose_name = "Auto Reply Rule"
    verbose_name_plural = "Auto Reply Rules"


class BusinessHoursInline(admin.TabularInline):
    model = BusinessHours
    extra = 0
    fields = ['day_of_week', 'open_time', 'close_time', 'is_open']
    ordering = ['day_of_week']
    can_delete = False
    verbose_name = "Business Hour"
    verbose_name_plural = "Business Hours"


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = [
        'business_name', 'email', 'whatsapp_number',
        'is_active', 'payment_status', 'plan',
        'token_status', 'rule_count', 'open_days', 'created_at'
    ]
    list_filter = ['is_active', 'token_valid', 'payment_status', 'plan']
    search_fields = ['business_name', 'email']
    inlines = [AutoReplyRuleInline, BusinessHoursInline]
    exclude = ['hashed_password']
    readonly_fields = ['created_at']
    actions = ['activate_clients']

    def rule_count(self, obj):
        return obj.rules.count()
    rule_count.short_description = 'Rules'

    def open_days(self, obj):
        count = obj.business_hours.filter(is_open=True).count()
        if count > 0:
            return f"✔ {count} days"
        return "✘ Not set"
    open_days.short_description = 'Hours'

    def token_status(self, obj):
        if obj.token_valid:
            return "✅ Valid"
        return "❌ Invalid"
    token_status.short_description = 'Token'

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


@admin.register(MessageLog)
class MessageLogAdmin(admin.ModelAdmin):
    list_display = ['client', 'sender_number', 'message_text', 'direction', 'timestamp']
    list_filter = ['direction', 'client']
    search_fields = ['sender_number', 'message_text']
    readonly_fields = ['client', 'sender_number', 'message_text', 'direction', 'timestamp']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'client', 'keyword', 'price', 'category', 'is_active', 'created_at']
    list_filter = ['is_active', 'client', 'category']
    search_fields = ['name', 'keyword', 'client__business_name']
    readonly_fields = ['created_at', 'image_url', 'image_public_id']


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ['client', 'has_welcome', 'has_menu', 'has_closed', 'has_handoff', 'has_fallback', 'updated_at']
    search_fields = ['client__business_name']
    readonly_fields = ['updated_at']

    def get_queryset(self, request):
        for client in Client.objects.all():
            MessageTemplate.objects.get_or_create(client=client)
        return super().get_queryset(request)

    def has_welcome(self, obj):
        return "✔" if obj.welcome_message else "✘"
    has_welcome.short_description = 'Welcome'

    def has_menu(self, obj):
        return "✔" if obj.menu_message else "✘"
    has_menu.short_description = 'Menu'

    def has_closed(self, obj):
        return "✔" if obj.closed_message else "✘"
    has_closed.short_description = 'Closed'

    def has_handoff(self, obj):
        return "✔" if obj.handoff_message else "✘"
    has_handoff.short_description = 'Handoff'

    def has_fallback(self, obj):
        return "✔" if obj.fallback_message else "✘"
    has_fallback.short_description = 'Fallback'


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['client', 'token_short', 'expires_at', 'used', 'created_at']
    list_filter = ['used', 'client']
    readonly_fields = ['client', 'token', 'expires_at', 'used', 'created_at']

    def token_short(self, obj):
        return f"{obj.token[:15]}..."
    token_short.short_description = 'Token'

    def has_add_permission(self, request):
        return False

list_display = [
    'business_name', 'email', 'whatsapp_number',
    'is_active', 'payment_status', 'plan',
    'subscription_end', 'days_remaining',
    'token_status', 'created_at'
]

def days_remaining(self, obj):
    if not obj.subscription_end:
        return "—"
    from datetime import date
    days = (obj.subscription_end - date.today()).days
    if days < 0:
        return f"❌ Expired {abs(days)}d ago"
    elif days <= 3:
        return f"🔴 {days}d left"
    elif days <= 7:
        return f"🟡 {days}d left"
    return f"🟢 {days}d left"
days_remaining.short_description = 'Subscription'

from .models import SubscriptionPlan

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display   = ['display_name', 'price_naira_display', 'is_active', 'updated_at']
    list_editable  = ['is_active']
    fields         = ['name', 'display_name', 'price_naira', 'description', 'is_active']
    readonly_fields = ['created_at', 'updated_at']

    def price_naira_display(self, obj):
        return f"₦{obj.price_naira:,}"
    price_naira_display.short_description = 'Price (₦)'

    def save_model(self, request, obj, form, change):
        """Auto-convert naira input to kobo if needed"""
        super().save_model(request, obj, form, change)


# core/admin.py — Add these to your existing admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import EmailCampaign, CampaignLog


# ─────────────────────────────────────────────
# CAMPAIGN LOG INLINE
# ─────────────────────────────────────────────

class CampaignLogInline(admin.TabularInline):
    model        = CampaignLog
    extra        = 0
    readonly_fields = ['client', 'email', 'status', 'sent_at', 'opened_at', 'error_msg']
    can_delete   = False
    max_num      = 0  # no adding manually
    show_change_link = False

    def has_add_permission(self, request, obj=None):
        return False


# ─────────────────────────────────────────────
# EMAIL CAMPAIGN ADMIN
# ─────────────────────────────────────────────

@admin.register(EmailCampaign)
class EmailCampaignAdmin(admin.ModelAdmin):

    list_display = [
        'subject', 'recipient_type', 'target_plan',
        'status_badge', 'progress_bar',
        'total_recipients', 'sent_count', 'failed_count',
        'scheduled_at', 'created_at'
    ]

    list_filter  = ['status', 'recipient_type', 'target_plan']
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
            'description': (
                'Choose "All Clients" to send to everyone, '
                '"By Plan" to filter by plan, or '
                '"Selected Clients" to hand-pick recipients.'
            )
        }),
        ('⏰ Scheduling', {
            'fields': ('scheduled_at',),
            'description': 'Leave blank to send immediately when you click Send Campaign.'
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

    actions = ['action_send_now', 'action_queue_campaign']

    # ── Custom display methods ──

    def status_badge(self, obj):
        colors = {
            'draft':     '#6c757d',
            'queued':    '#fd7e14',
            'sending':   '#0d6efd',
            'completed': '#198754',
            'failed':    '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;'
            'border-radius:20px;font-size:0.8rem;font-weight:600;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def progress_bar(self, obj):
        pct = obj.progress_percent
        color = '#198754' if pct == 100 else '#0d6efd'
        return format_html(
            '<div style="width:120px;background:#e9ecef;border-radius:4px;height:16px;">'
            '<div style="width:{}%;background:{};height:100%;border-radius:4px;'
            'transition:width 0.3s;"></div></div>'
            '<small style="color:#666;">{}%</small>',
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
            pct,
            obj.sent_count,
            obj.failed_count,
            pct
        )
    progress_display.short_description = 'Progress'

    # ── Admin actions ──

    @admin.action(description='📤 Send now (immediately)')
    def action_send_now(self, request, queryset):
        from core.tasks import send_campaign

        count = 0
        for campaign in queryset.filter(status__in=['draft', 'queued']):
            campaign.status      = 'queued'
            campaign.scheduled_at = None
            campaign.save(update_fields=['status', 'scheduled_at'])
            send_campaign.delay(campaign.id)
            count += 1

        self.message_user(
            request,
            f"✅ {count} campaign(s) queued and sending in background."
        )

    @admin.action(description='📋 Mark as queued (will send at scheduled time)')
    def action_queue_campaign(self, request, queryset):
        count = queryset.filter(status='draft').update(status='queued')
        self.message_user(request, f"✅ {count} campaign(s) marked as queued.")


# ─────────────────────────────────────────────
# CAMPAIGN LOG ADMIN (view only)
# ─────────────────────────────────────────────

@admin.register(CampaignLog)
class CampaignLogAdmin(admin.ModelAdmin):
    list_display  = ['campaign', 'email', 'status', 'sent_at', 'opened_at']
    list_filter   = ['status', 'campaign']
    search_fields = ['email', 'campaign__subject']
    readonly_fields = ['campaign', 'client', 'email', 'status', 'sent_at', 'opened_at', 'error_msg']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False