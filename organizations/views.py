"""
Organization views: dashboard, branch registration, branch performance.
All views enforce organization-level ownership via RBAC mixins.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.db.models import Count, Q, Avg

from core.mixins import OrganizationRequiredMixin
from core.roles import BRANCH
from accounts.models import User
from facilities.models import Branch, Service


class OrganizationDashboardView(OrganizationRequiredMixin, View):
    """Organization dashboard showing branches and stats."""

    def get(self, request):
        org = request.user.organization
        branches = Branch.objects.filter(organization=org)
        context = {
            'organization': org,
            'branches': branches,
            'total_branches': branches.count(),
            'active_branches': branches.filter(is_active=True).count(),
        }
        return render(request, 'organization/dashboard.html', context)


class RegisterBranchView(OrganizationRequiredMixin, View):
    """Register a new branch under the organization."""

    def get(self, request):
        return render(request, 'organization/register_branch.html', {
            'organization': request.user.organization,
        })

    def post(self, request):
        org = request.user.organization
        name = request.POST.get('name', '').strip()
        address = request.POST.get('address', '').strip()
        branch_username = request.POST.get('branch_username', '').strip()
        branch_password = request.POST.get('branch_password', '')

        errors = []
        if not name:
            errors.append('Branch name is required.')
        if not branch_username:
            errors.append('Branch username is required.')
        if not branch_password or len(branch_password) < 8:
            errors.append('Branch password must be at least 8 characters.')
        if User.objects.filter(username=branch_username).exists():
            errors.append('Username already taken.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'organization/register_branch.html', {
                'organization': org,
                'name': name,
                'address': address,
                'branch_username': branch_username,
            })

        branch = Branch.objects.create(
            name=name,
            organization=org,
            address=address,
        )

        User.objects.create_user(
            username=branch_username,
            password=branch_password,
            role=BRANCH,
            organization=org,
            branch=branch,
        )

        messages.success(request, f'Branch "{name}" created successfully.')
        return redirect('organizations:dashboard')


class BranchPerformanceView(OrganizationRequiredMixin, View):
    """View performance stats for branches in the organization."""

    def get(self, request):
        org = request.user.organization
        branches = Branch.objects.filter(organization=org).annotate(
            service_count=Count('services'),
            counter_count=Count('counters'),
        )
        context = {
            'organization': org,
            'branches': branches,
        }
        return render(request, 'organization/branch_performance.html', context)
