from django.contrib import admin
from .models import NotificationLog


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('notification_type', 'recipient', 'recipient_mobile', 'status', 'retries', 'created_at')
    list_filter = ('notification_type', 'status')
    search_fields = ('recipient_mobile', 'message')
    readonly_fields = ('created_at',)
