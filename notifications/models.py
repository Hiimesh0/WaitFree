"""
NotificationLog model: tracks all notifications (OTP, turn alerts).
"""

from django.db import models
from django.conf import settings


class NotificationLog(models.Model):
    TYPE_CHOICES = [
        ('otp', 'OTP'),
        ('turn_alert', 'Turn Alert'),
    ]
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('retried', 'Retried'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
    )
    recipient_mobile = models.CharField(max_length=15, blank=True)
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    retries = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'waitfree_notification_log'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} to {self.recipient_mobile or self.recipient} ({self.status})"
