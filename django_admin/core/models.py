from django.db import models
import secrets
from django.utils import timezone
from datetime import timedelta
from datetime import datetime

def is_valid(self):
    now = datetime.now()  # naive datetime to match database
    return not self.used and now < self.expires_at
class Client(models.Model):
    business_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    hashed_password = models.CharField(max_length=255)
    phone_number_id = models.CharField(max_length=255, unique=True)
    whatsapp_number = models.CharField(max_length=50)
    access_token = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    token_valid = models.BooleanField(default=True)
    plan = models.CharField(max_length=20, default='starter')
    payment_status = models.CharField(max_length=20, default='unpaid')
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    waba_id = models.CharField(max_length=100, blank=True, null=True)
    subscription_start = models.DateField(null=True, blank=True)
    subscription_end = models.DateField(null=True, blank=True)
    grace_period_end = models.DateField(null=True, blank=True)
    reminder_7_sent = models.BooleanField(default=False)
    reminder_3_sent = models.BooleanField(default=False)
    ai_replies_used = models.IntegerField(default=0)
    ai_replies_reset_date = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'clients'  # reuse existing table

    def __str__(self):
        return self.business_name


class AutoReplyRule(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='rules')
    trigger_keyword = models.CharField(max_length=255)
    response_text = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auto_reply_rules'  # reuse existing table

    def __str__(self):
        return f"{self.client.business_name} - {self.trigger_keyword}"


class MessageLog(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='messages')
    sender_number = models.CharField(max_length=50)
    message_text = models.TextField()
    direction = models.CharField(max_length=10)  # inbound / outbound
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'message_logs'  # reuse existing table

    def __str__(self):
        return f"{self.direction} - {self.sender_number}"

class Contact(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=50)
    opted_out = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'contacts'

    def __str__(self):
        return f"{self.name} - {self.phone_number}"

    class Meta:
        db_table = 'contacts'

    def __str__(self):
        return f"{self.name} - {self.phone_number}"


class Broadcast(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='broadcasts')
    title = models.CharField(max_length=255)
    message = models.TextField()
    template_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, default='pending')
    total = models.IntegerField(default=0)
    sent = models.IntegerField(default=0)
    failed = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'broadcasts'

    def __str__(self):
        return self.title

class BusinessHours(models.Model):
    DAYS = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='business_hours')
    day_of_week = models.IntegerField(choices=DAYS)
    open_time = models.CharField(max_length=5)
    close_time = models.CharField(max_length=5)
    is_open = models.BooleanField(default=True)

    class Meta:
        db_table = 'business_hours'
        verbose_name = "Business Hour"
        verbose_name_plural = "Business Hours"  # Fixes the "hourss" typo

    def __str__(self):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return f"{self.client.business_name} - {days[self.day_of_week]}"
class Product(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.CharField(max_length=100)
    image_url = models.URLField(blank=True, null=True)
    image_public_id = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    keyword = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'products'

    def __str__(self):
        return f"{self.client.business_name} - {self.name}"
    
class MessageTemplate(models.Model):
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='message_template')
    welcome_message = models.TextField(blank=True, null=True)
    menu_message = models.TextField(blank=True, null=True)
    closed_message = models.TextField(blank=True, null=True)
    handoff_message = models.TextField(blank=True, null=True)
    fallback_message = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'message_templates'

    def __str__(self):
        return f"{self.client.business_name} - Templates"
    


class PasswordResetToken(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=100, unique=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'password_reset_tokens'

    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at

    def __str__(self):
        return f"{self.client.business_name} - {self.token[:10]}..."


class SubscriptionPlan(models.Model):
    name         = models.CharField(max_length=20, unique=True)
    display_name = models.CharField(max_length=100)
    price_kobo   = models.IntegerField(editable=False)  # hidden
    price_naira  = models.IntegerField(
        default=0,
        help_text="Enter price in Naira (e.g. 8000). We'll convert to kobo automatically."
    )
    description  = models.TextField(blank=True)
    is_active    = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-convert naira to kobo on save
        self.price_kobo = self.price_naira * 100
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.display_name} — ₦{self.price_naira:,}"

    class Meta:
        db_table = 'subscription_plans'

# ─────────────────────────────────────────────
# Add these two models to the bottom of core/models.py
# ─────────────────────────────────────────────

class EmailCampaign(models.Model):

    RECIPIENT_CHOICES = [
        ('all',      'All Clients'),
        ('plan',     'By Plan'),
        ('selected', 'Selected Clients'),
    ]

    STATUS_CHOICES = [
        ('draft',     'Draft'),
        ('queued',    'Queued'),
        ('sending',   'Sending'),
        ('completed', 'Completed'),
        ('failed',    'Failed'),
    ]

    subject            = models.CharField(max_length=255)
    body               = models.TextField(help_text="HTML supported")
    recipient_type     = models.CharField(max_length=20, choices=RECIPIENT_CHOICES, default='all')
    target_plan        = models.CharField(
                            max_length=20,
                            blank=True, null=True,
                            help_text="Only used when recipient type is 'By Plan'"
                         )
    selected_clients   = models.ManyToManyField(
                            'Client',
                            blank=True,
                            related_name='campaigns',
                            help_text="Only used when recipient type is 'Selected Clients'"
                         )
    scheduled_at       = models.DateTimeField(
                            blank=True, null=True,
                            help_text="Leave blank to send immediately"
                         )
    status             = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_recipients   = models.IntegerField(default=0)
    sent_count         = models.IntegerField(default=0)
    failed_count       = models.IntegerField(default=0)
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'email_campaigns'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} — {self.status}"

    @property
    def progress_percent(self):
        if self.total_recipients == 0:
            return 0
        return int((self.sent_count / self.total_recipients) * 100)


class CampaignLog(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent',    'Sent'),
        ('failed',  'Failed'),
        ('opened',  'Opened'),
    ]

    campaign   = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE, related_name='logs')
    client     = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='campaign_logs')
    email      = models.EmailField()
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at    = models.DateTimeField(blank=True, null=True)
    opened_at  = models.DateTimeField(blank=True, null=True)
    error_msg  = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'campaign_logs'
        unique_together = ('campaign', 'client')

    def __str__(self):
        return f"{self.campaign.subject} → {self.email} [{self.status}]"