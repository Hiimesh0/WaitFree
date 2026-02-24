"""
Operator views: dashboard, counter open/close.
All views enforce operator role and counter assignment.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.utils import timezone

from core.mixins import OperatorRequiredMixin
from .models import Counter, OperatorAssignment


class OperatorDashboardView(OperatorRequiredMixin, View):
    """Operator dashboard showing assigned counter and queue status."""

    def get(self, request):
        try:
            assignment = request.user.operator_assignment
            counter = assignment.counter
        except OperatorAssignment.DoesNotExist:
            return render(request, 'operator/dashboard.html', {
                'has_assignment': False,
            })

        from queues.models import QueueTicket
        waiting_tickets = QueueTicket.objects.filter(
            service=counter.service,
            branch=counter.branch,
            status='waiting',
        ).order_by('joined_at')

        current_ticket = QueueTicket.objects.filter(
            service=counter.service,
            branch=counter.branch,
            status='serving',
        ).first()

        context = {
            'has_assignment': True,
            'counter': counter,
            'service': counter.service,
            'waiting_tickets': waiting_tickets,
            'waiting_count': waiting_tickets.count(),
            'current_ticket': current_ticket,
        }
        return render(request, 'operator/dashboard.html', context)


class CounterControlView(OperatorRequiredMixin, View):
    """Open or close the operator's assigned counter."""

    def post(self, request):
        try:
            assignment = request.user.operator_assignment
            counter = assignment.counter
        except OperatorAssignment.DoesNotExist:
            messages.error(request, 'You are not assigned to any counter.')
            return redirect('counters:operator_dashboard')

        action = request.POST.get('action')
        if action == 'open':
            counter.is_open = True
            counter.save()
            messages.success(request, f'Counter {counter.number} is now OPEN.')
        elif action == 'close':
            counter.is_open = False
            counter.save()
            messages.success(request, f'Counter {counter.number} is now CLOSED.')

        # Recalculate ETAs for all waiting tickets in this service
        from queues.engine import recalculate_eta
        recalculate_eta(counter.service)

        return redirect('counters:operator_dashboard')
