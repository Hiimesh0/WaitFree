"""
Facility views: branch dashboard, service CRUD, citizen-facing search.
All views enforce RBAC at view level via mixins.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.db.models import Q, Count

from core.mixins import BranchRequiredMixin, CitizenRequiredMixin, RoleRequiredMixin
from core.roles import BRANCH, CITIZEN, OPERATOR
from accounts.models import User
from .models import Branch, Service
from counters.models import Counter, OperatorAssignment


class BranchDashboardView(BranchRequiredMixin, View):
    """Branch manager dashboard."""

    def get(self, request):
        branch = request.user.branch
        services = Service.objects.filter(branch=branch)
        counters = Counter.objects.filter(branch=branch)

        from queues.models import QueueTicket
        active_tickets = QueueTicket.objects.filter(
            branch=branch,
            status__in=['waiting', 'serving'],
        )

        context = {
            'branch': branch,
            'services': services,
            'counters': counters,
            'total_services': services.count(),
            'total_counters': counters.count(),
            'open_counters': counters.filter(is_open=True).count(),
            'waiting_count': active_tickets.filter(status='waiting').count(),
            'serving_count': active_tickets.filter(status='serving').count(),
        }
        return render(request, 'branch/dashboard.html', context)


class ManageServicesView(BranchRequiredMixin, View):
    """CRUD for services under the branch."""

    def get(self, request):
        branch = request.user.branch
        services = Service.objects.filter(branch=branch)
        return render(request, 'branch/manage_services.html', {
            'branch': branch,
            'services': services,
        })

    def post(self, request):
        branch = request.user.branch
        action = request.POST.get('action')

        if action == 'create':
            name = request.POST.get('name', '').strip()
            avg_time = request.POST.get('avg_service_time', '10')
            description = request.POST.get('description', '').strip()

            if not name:
                messages.error(request, 'Service name is required.')
            elif Service.objects.filter(name=name, branch=branch).exists():
                messages.error(request, 'Service with this name already exists.')
            else:
                Service.objects.create(
                    name=name,
                    branch=branch,
                    avg_service_time=int(avg_time),
                    description=description,
                )
                messages.success(request, f'Service "{name}" created.')

        elif action == 'toggle':
            service_id = request.POST.get('service_id')
            service = get_object_or_404(Service, id=service_id, branch=branch)
            service.is_active = not service.is_active
            service.save()
            status = 'activated' if service.is_active else 'deactivated'
            messages.success(request, f'Service "{service.name}" {status}.')

        elif action == 'delete':
            service_id = request.POST.get('service_id')
            service = get_object_or_404(Service, id=service_id, branch=branch)
            service.delete()
            messages.success(request, f'Service deleted.')

        return redirect('facilities:manage_services')


class ManageCountersView(BranchRequiredMixin, View):
    """CRUD for counters under the branch."""

    def get(self, request):
        branch = request.user.branch
        counters = Counter.objects.filter(branch=branch).select_related('service', 'current_operator')
        services = Service.objects.filter(branch=branch, is_active=True)
        return render(request, 'branch/manage_counters.html', {
            'branch': branch,
            'counters': counters,
            'services': services,
        })

    def post(self, request):
        branch = request.user.branch
        action = request.POST.get('action')

        if action == 'create':
            number = request.POST.get('number', '').strip()
            service_id = request.POST.get('service_id')

            if not number:
                messages.error(request, 'Counter number is required.')
            else:
                service = get_object_or_404(Service, id=service_id, branch=branch)
                if Counter.objects.filter(number=number, branch=branch).exists():
                    messages.error(request, 'Counter with this number already exists.')
                else:
                    Counter.objects.create(
                        number=number,
                        branch=branch,
                        service=service,
                    )
                    messages.success(request, f'Counter {number} created.')

        elif action == 'delete':
            counter_id = request.POST.get('counter_id')
            counter = get_object_or_404(Counter, id=counter_id, branch=branch)
            counter.delete()
            messages.success(request, 'Counter deleted.')

        return redirect('facilities:manage_counters')


class ManageOperatorsView(BranchRequiredMixin, View):
    """CRUD for operators under the branch."""

    def get(self, request):
        branch = request.user.branch
        operators = User.objects.filter(role=OPERATOR, branch=branch)
        counters = Counter.objects.filter(branch=branch)
        assignments = OperatorAssignment.objects.filter(counter__branch=branch).select_related('user', 'counter')
        return render(request, 'branch/manage_operators.html', {
            'branch': branch,
            'operators': operators,
            'counters': counters,
            'assignments': assignments,
        })

    def post(self, request):
        branch = request.user.branch
        action = request.POST.get('action')

        if action == 'create':
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')
            counter_id = request.POST.get('counter_id')

            if not username or not password:
                messages.error(request, 'Username and password are required.')
            elif User.objects.filter(username=username).exists():
                messages.error(request, 'Username already taken.')
            else:
                operator = User.objects.create_user(
                    username=username,
                    password=password,
                    role=OPERATOR,
                    organization=branch.organization,
                    branch=branch,
                )
                if counter_id:
                    counter = get_object_or_404(Counter, id=counter_id, branch=branch)
                    OperatorAssignment.objects.create(user=operator, counter=counter)
                    counter.current_operator = operator
                    counter.save()
                messages.success(request, f'Operator "{username}" created.')

        elif action == 'assign':
            operator_id = request.POST.get('operator_id')
            counter_id = request.POST.get('counter_id')
            operator = get_object_or_404(User, id=operator_id, role=OPERATOR, branch=branch)
            counter = get_object_or_404(Counter, id=counter_id, branch=branch)

            # Remove existing assignment
            OperatorAssignment.objects.filter(user=operator).delete()
            Counter.objects.filter(current_operator=operator).update(current_operator=None)

            OperatorAssignment.objects.create(user=operator, counter=counter)
            counter.current_operator = operator
            counter.save()
            messages.success(request, f'Operator "{operator.username}" assigned to Counter {counter.number}.')

        elif action == 'delete':
            operator_id = request.POST.get('operator_id')
            operator = get_object_or_404(User, id=operator_id, role=OPERATOR, branch=branch)
            operator.delete()
            messages.success(request, 'Operator deleted.')

        return redirect('facilities:manage_operators')


class LiveQueueMonitorView(BranchRequiredMixin, View):
    """Live queue monitor for branch managers."""

    def get(self, request):
        branch = request.user.branch
        from queues.models import QueueTicket

        services = Service.objects.filter(branch=branch, is_active=True)
        counters = Counter.objects.filter(branch=branch).select_related('service', 'current_operator')

        queue_data = []
        for service in services:
            tickets = QueueTicket.objects.filter(
                service=service,
                branch=branch,
                status__in=['waiting', 'serving'],
            ).order_by('joined_at')
            queue_data.append({
                'service': service,
                'tickets': tickets,
                'waiting': tickets.filter(status='waiting').count(),
                'serving': tickets.filter(status='serving').count(),
            })

        context = {
            'branch': branch,
            'counters': counters,
            'queue_data': queue_data,
        }
        return render(request, 'branch/live_monitor.html', context)


class FacilitySearchView(View):
    """Public facility search for citizens."""

    def get(self, request):
        query = request.GET.get('q', '').strip()
        branches = Branch.objects.filter(is_active=True)
        if query:
            branches = branches.filter(
                Q(name__icontains=query) |
                Q(organization__name__icontains=query) |
                Q(city__icontains=query) |
                Q(address__icontains=query)
            )
        branches = branches.select_related('organization')
        return render(request, 'citizen/facility_search.html', {
            'branches': branches,
            'query': query,
        })


class BranchDetailView(View):
    """Branch detail view for citizens showing services and queue status."""

    def get(self, request, branch_id):
        branch = get_object_or_404(Branch, id=branch_id, is_active=True)
        services = Service.objects.filter(branch=branch, is_active=True)

        service_data = []
        for service in services:
            from queues.models import QueueTicket
            waiting_count = QueueTicket.objects.filter(
                service=service, status='waiting'
            ).count()
            open_counters = Counter.objects.filter(
                service=service, is_open=True
            ).count()
            service_data.append({
                'service': service,
                'waiting_count': waiting_count,
                'open_counters': open_counters,
            })

        context = {
            'branch': branch,
            'service_data': service_data,
        }
        return render(request, 'citizen/branch_detail.html', context)
