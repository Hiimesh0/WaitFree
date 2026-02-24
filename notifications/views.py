"""
Notification views: citizen notification listing.
"""

from django.shortcuts import render
from django.views import View
from core.mixins import CitizenRequiredMixin
from .models import NotificationLog


class CitizenNotificationsView(CitizenRequiredMixin, View):
    """Citizen views their notification history."""

    def get(self, request):
        notifications = NotificationLog.objects.filter(
            recipient=request.user,
        ).order_by('-created_at')[:50]

        return render(request, 'citizen/notifications.html', {
            'notifications': notifications,
        })
