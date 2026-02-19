from django.db import models

class Client(models.Model):
    business_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    hashed_password = models.CharField(max_length=255)
    phone_number_id = models.CharField(max_length=255, unique=True)
    whatsapp_number = models.CharField(max_length=50)
    access_token = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

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
    created_at = models.DateTimeField(auto_now_add=True)

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

    def __str__(self):
        return f"{self.client.business_name} - {self.get_day_of_week_display()}"