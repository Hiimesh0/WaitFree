from django.contrib import admin
from .models import QueueTicket


@admin.register(QueueTicket)
class QueueTicketAdmin(admin.ModelAdmin):
    list_display = ('token_number', 'citizen', 'service', 'branch', 'status', 'position',
                    'estimated_wait_time', 'joined_at', 'called_at', 'served_at')
    list_filter = ('status', 'branch', 'service')
    search_fields = ('token_number', 'citizen__username', 'citizen__mobile_number')
    readonly_fields = ('joined_at', 'called_at', 'served_at', 'no_show_at')
