"""
QueueTicket model: tracks every citizen's position in a queue.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class QueueTicket(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('serving', 'Being Served'),
        ('served', 'Served'),
        ('no_show', 'No Show'),
    ]

    citizen = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='queue_tickets',
    )
    service = models.ForeignKey(
        'facilities.Service',
        on_delete=models.CASCADE,
        related_name='queue_tickets',
    )
    branch = models.ForeignKey(
        'facilities.Branch',
        on_delete=models.CASCADE,
        related_name='queue_tickets',
    )
    token_number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    position = models.PositiveIntegerField(default=0)
    estimated_wait_time = models.IntegerField(
        default=0,
        help_text='Estimated wait time in minutes',
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    called_at = models.DateTimeField(null=True, blank=True)
    served_at = models.DateTimeField(null=True, blank=True)
    no_show_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'waitfree_queue_ticket'
        ordering = ['joined_at']
        indexes = [
            models.Index(fields=['service', 'status', 'joined_at']),
            models.Index(fields=['branch', 'status']),
            models.Index(fields=['citizen', 'status']),
        ]

    def __str__(self):
        return f"Token #{self.token_number} - {self.citizen} ({self.status})"

    @property
    def is_active(self):
        return self.status in ('waiting', 'serving')

    @property
    def wait_duration_minutes(self):
        """Actual wait duration from join to call/now."""
        end_time = self.called_at or timezone.now()
        delta = end_time - self.joined_at
        return int(delta.total_seconds() / 60)
