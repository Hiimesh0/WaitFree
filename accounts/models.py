"""
Custom User model with role-based authentication.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from core.roles import ROLE_CHOICES, CITIZEN


class User(AbstractUser):
    """
    Custom user model supporting multiple roles.
    Citizens authenticate via mobile + OTP.
    All others authenticate via username + password.
    """
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=CITIZEN)
    mobile_number = models.CharField(max_length=15, blank=True, null=True, unique=True)
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
    )
    branch = models.ForeignKey(
        'facilities.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
    )

    class Meta:
        db_table = 'waitfree_user'

    def __str__(self):
        if self.role == CITIZEN and self.mobile_number:
            return f"Citizen ({self.mobile_number})"
        return f"{self.get_role_display()} - {self.username}"

    @property
    def is_global_admin(self):
        return self.role == 'global_admin'

    @property
    def is_organization_user(self):
        return self.role == 'organization'

    @property
    def is_branch_user(self):
        return self.role == 'branch'

    @property
    def is_operator_user(self):
        return self.role == 'operator'

    @property
    def is_citizen_user(self):
        return self.role == 'citizen'
