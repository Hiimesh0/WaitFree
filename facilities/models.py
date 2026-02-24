"""
Branch and Service models.
Hierarchy: Organization → Branch → Service
"""

from django.db import models


class Branch(models.Model):
    """A physical branch/location belonging to an organization."""
    name = models.CharField(max_length=255)
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='branches',
    )
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'waitfree_branch'
        ordering = ['name']
        verbose_name_plural = 'branches'

    def __str__(self):
        return f"{self.name} ({self.organization.name})"

    @property
    def active_counter_count(self):
        return self.counters.filter(is_open=True).count()


class Service(models.Model):
    """A service offered at a branch (e.g., General Consultation, Billing)."""
    name = models.CharField(max_length=255)
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='services',
    )
    description = models.TextField(blank=True)
    avg_service_time = models.PositiveIntegerField(
        default=10,
        help_text='Average service time in minutes',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'waitfree_service'
        ordering = ['name']
        unique_together = ['name', 'branch']

    def __str__(self):
        return f"{self.name} @ {self.branch.name}"

    @property
    def active_counter_count(self):
        return self.counters.filter(is_open=True).count()

    @property
    def waiting_count(self):
        return self.queue_tickets.filter(status='waiting').count()
