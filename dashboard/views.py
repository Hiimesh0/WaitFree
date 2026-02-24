"""
Dashboard views: role-based routing to appropriate dashboards.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.db.models import Count, Q

from core.mixins import GlobalAdminRequiredMixin
from core.roles import GLOBAL_ADMIN, ORGANIZATION, BRANCH, OPERATOR, CITIZEN
from organizations.models import Organization
from facilities.models import Branch, Service
from counters.models import Counter
from queues.models import QueueTicket


class DashboardRouterView(LoginRequiredMixin, View):
    """Redirects to the appropriate dashboard based on user role."""

    def get(self, request):
        role = request.user.role
        if role == GLOBAL_ADMIN:
            return redirect('dashboard:admin_dashboard')
        elif role == ORGANIZATION:
            return redirect('organizations:dashboard')
        elif role == BRANCH:
            return redirect('facilities:branch_dashboard')
        elif role == OPERATOR:
            return redirect('counters:operator_dashboard')
        elif role == CITIZEN:
            return redirect('dashboard:citizen_dashboard')
        return redirect('landing')


class AdminDashboardView(GlobalAdminRequiredMixin, View):
    """Admin dashboard with global monitoring."""

    def get(self, request):
        context = {
            'total_orgs': Organization.objects.count(),
            'active_orgs': Organization.objects.filter(is_active=True).count(),
            'total_branches': Branch.objects.count(),
            'active_branches': Branch.objects.filter(is_active=True).count(),
            'total_counters': Counter.objects.count(),
            'open_counters': Counter.objects.filter(is_open=True).count(),
            'today_tickets': QueueTicket.objects.filter(
                joined_at__date=__import__('django.utils', fromlist=['timezone']).timezone.localdate()
            ).count(),
            'waiting_now': QueueTicket.objects.filter(status='waiting').count(),
            'serving_now': QueueTicket.objects.filter(status='serving').count(),
        }
        return render(request, 'admin_panel/dashboard.html', context)


class ManageOrganizationsView(GlobalAdminRequiredMixin, View):
    """Admin manages organizations."""

    def get(self, request):
        orgs = Organization.objects.annotate(
            branch_count_val=Count('branches'),
        )
        return render(request, 'admin_panel/manage_orgs.html', {'organizations': orgs})

    def post(self, request):
        action = request.POST.get('action')
        org_id = request.POST.get('org_id')

        if action == 'toggle' and org_id:
            from django.contrib import messages
            org = Organization.objects.get(id=org_id)
            org.is_active = not org.is_active
            org.save()
            status = 'activated' if org.is_active else 'deactivated'
            messages.success(request, f'Organization "{org.name}" {status}.')

        return redirect('dashboard:manage_orgs')


class GlobalMonitorView(GlobalAdminRequiredMixin, View):
    """Global queue monitoring across all organizations."""

    def get(self, request):
        branches = Branch.objects.filter(is_active=True).select_related('organization').annotate(
            waiting_count=Count('queue_tickets', filter=Q(queue_tickets__status='waiting')),
            serving_count=Count('queue_tickets', filter=Q(queue_tickets__status='serving')),
        )
        return render(request, 'admin_panel/global_monitor.html', {
            'branches': branches,
        })


class SystemHealthView(GlobalAdminRequiredMixin, View):
    """System health and stats."""

    def get(self, request):
        from django.utils import timezone
        from datetime import timedelta
        from accounts.models import User

        now = timezone.now()
        today = timezone.localdate()

        context = {
            'total_users': User.objects.count(),
            'citizen_count': User.objects.filter(role=CITIZEN).count(),
            'operator_count': User.objects.filter(role=OPERATOR).count(),
            'total_tickets_today': QueueTicket.objects.filter(joined_at__date=today).count(),
            'served_today': QueueTicket.objects.filter(status='served', served_at__date=today).count(),
            'no_show_today': QueueTicket.objects.filter(status='no_show', no_show_at__date=today).count(),
            'total_orgs': Organization.objects.count(),
            'total_branches': Branch.objects.count(),
            'total_services': Service.objects.count(),
            'total_counters': Counter.objects.count(),
        }
        return render(request, 'admin_panel/system_health.html', context)


class CitizenDashboardView(View):
    """Citizen dashboard showing active tickets and facility search."""

    def get(self, request):
        if not request.user.is_authenticated or request.user.role != CITIZEN:
            return redirect('accounts:login')

        active_tickets = QueueTicket.objects.filter(
            citizen=request.user,
            status__in=['waiting', 'serving'],
        ).select_related('service', 'branch')

        return render(request, 'citizen/dashboard.html', {
            'active_tickets': active_tickets,
        })
