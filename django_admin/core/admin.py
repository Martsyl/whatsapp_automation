from django.contrib import admin
from .models import Client, AutoReplyRule, MessageLog, BusinessHours
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AutoReplyRuleInline(admin.TabularInline):
    model = AutoReplyRule
    extra = 1
    fields = ['trigger_keyword', 'response_text', 'is_active']
    can_delete = True


class BusinessHoursInline(admin.TabularInline):
    model = BusinessHours
    extra = 7


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'email', 'whatsapp_number', 'is_active', 'rule_count', 'created_at']
    list_filter = ['is_active']
    search_fields = ['business_name', 'email']
    inlines = [AutoReplyRuleInline, BusinessHoursInline]
    exclude = ['hashed_password']
    readonly_fields = ['created_at']

    def rule_count(self, obj):
        return obj.rules.count()
    rule_count.short_description = 'Rules'


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