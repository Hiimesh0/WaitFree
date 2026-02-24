"""
DRF permission classes for RBAC enforcement.
Every request validates role, organization ownership, branch ownership, counter assignment.
"""

from rest_framework.permissions import BasePermission
from core.roles import GLOBAL_ADMIN, ORGANIZATION, BRANCH, OPERATOR, CITIZEN


class IsGlobalAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == GLOBAL_ADMIN
        )


class IsOrganization(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == ORGANIZATION
        )


class IsBranch(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == BRANCH
        )


class IsOperator(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == OPERATOR
        )


class IsCitizen(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == CITIZEN
        )


class BelongsToOrganization(BasePermission):
    """Ensures the user can only access resources in their own organization."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role == GLOBAL_ADMIN:
            return True
        return request.user.organization is not None

    def has_object_permission(self, request, view, obj):
        if request.user.role == GLOBAL_ADMIN:
            return True
        obj_org = getattr(obj, 'organization', None)
        if obj_org is None and hasattr(obj, 'branch'):
            obj_org = obj.branch.organization if obj.branch else None
        return obj_org == request.user.organization


class BelongsToBranch(BasePermission):
    """Ensures the user can only access resources in their own branch."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role in (GLOBAL_ADMIN, ORGANIZATION):
            return True
        return request.user.branch is not None

    def has_object_permission(self, request, view, obj):
        if request.user.role == GLOBAL_ADMIN:
            return True
        if request.user.role == ORGANIZATION:
            obj_org = getattr(obj, 'organization', None)
            if obj_org is None and hasattr(obj, 'branch'):
                obj_org = obj.branch.organization if obj.branch else None
            return obj_org == request.user.organization
        obj_branch = getattr(obj, 'branch', None)
        return obj_branch == request.user.branch


class IsOperatorAssignedToCounter(BasePermission):
    """Validates operator → counter assignment."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role != OPERATOR:
            return False
        return hasattr(request.user, 'operator_assignment')
