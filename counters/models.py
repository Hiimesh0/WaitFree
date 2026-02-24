"""
Counter and OperatorAssignment models.
Hierarchy: Branch → Counter → Operator (one operator per counter, immutable assignment).
"""

from django.db import models
from django.conf import settings


class Counter(models.Model):
    """A service counter at a branch, assigned to a specific service."""
    number = models.CharField(max_length=20)
    branch = models.ForeignKey(
        'facilities.Branch',
        on_delete=models.CASCADE,
        related_name='counters',
    )
    service = models.ForeignKey(
        'facilities.Service',
        on_delete=models.CASCADE,
        related_name='counters',
    )
    is_open = models.BooleanField(default=False)
    current_operator = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_counter',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'waitfree_counter'
        unique_together = ['number', 'branch']
        ordering = ['number']

    def __str__(self):
        return f"Counter {self.number} @ {self.branch.name} ({self.service.name})"


class OperatorAssignment(models.Model):
    """
    Assigns exactly one operator to exactly one counter.
    This assignment cannot be changed by the operator.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='operator_assignment',
    )
    counter = models.OneToOneField(
        Counter,
        on_delete=models.CASCADE,
        related_name='assignment',
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'waitfree_operator_assignment'

    def __str__(self):
        return f"{self.user.username} → Counter {self.counter.number}"
