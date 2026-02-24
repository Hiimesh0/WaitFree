"""
Django CBV mixins for template-based views with RBAC enforcement.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from core.roles import GLOBAL_ADMIN, ORGANIZATION, BRANCH, OPERATOR, CITIZEN


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin that checks if user has one of the allowed roles."""
    allowed_roles = []

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        return self.request.user.role in self.allowed_roles

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("You do not have permission to access this page.")
        return super().handle_no_permission()


class GlobalAdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = [GLOBAL_ADMIN]


class OrganizationRequiredMixin(RoleRequiredMixin):
    allowed_roles = [ORGANIZATION]


class BranchRequiredMixin(RoleRequiredMixin):
    allowed_roles = [BRANCH]


class OperatorRequiredMixin(RoleRequiredMixin):
    allowed_roles = [OPERATOR]


class CitizenRequiredMixin(RoleRequiredMixin):
    allowed_roles = [CITIZEN]


class OrganizationFilterMixin:
    """Auto-filters querysets to the user's organization."""

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == GLOBAL_ADMIN:
            return qs
        if user.organization:
            if hasattr(qs.model, 'organization'):
                return qs.filter(organization=user.organization)
            if hasattr(qs.model, 'branch'):
                return qs.filter(branch__organization=user.organization)
        return qs.none()


class BranchFilterMixin:
    """Auto-filters querysets to the user's branch."""

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == GLOBAL_ADMIN:
            return qs
        if user.role == ORGANIZATION and user.organization:
            if hasattr(qs.model, 'branch'):
                return qs.filter(branch__organization=user.organization)
            if hasattr(qs.model, 'organization'):
                return qs.filter(organization=user.organization)
            return qs
        if user.branch:
            if hasattr(qs.model, 'branch'):
                return qs.filter(branch=user.branch)
        return qs.none()
