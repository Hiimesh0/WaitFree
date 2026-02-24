"""
Queue views: join queue, ticket view, queue overview, serve next, mark no-show.
All views enforce RBAC.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View

from core.mixins import CitizenRequiredMixin, OperatorRequiredMixin
from core.roles import CITIZEN
from .models import QueueTicket
from . import engine
from facilities.models import Service
from counters.models import OperatorAssignment


class JoinQueueView(CitizenRequiredMixin, View):
    """Citizen joins a queue for a service. Requires authenticated citizen."""

    def post(self, request):
        service_id = request.POST.get('service_id')
        service = get_object_or_404(Service, id=service_id, is_active=True)

        try:
            ticket = engine.join_queue(request.user, service)
            messages.success(request, f'Joined queue! Your token number is #{ticket.token_number}')
            return redirect('queues:ticket', ticket_id=ticket.id)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('facilities:branch_detail', branch_id=service.branch.id)


class QueueTicketView(CitizenRequiredMixin, View):
    """Citizen views their queue ticket."""

    def get(self, request, ticket_id):
        ticket = get_object_or_404(QueueTicket, id=ticket_id, citizen=request.user)
        return render(request, 'citizen/ticket.html', {'ticket': ticket})


class QueueOverviewView(View):
    """Public queue overview for a service."""

    def get(self, request, service_id):
        service = get_object_or_404(Service, id=service_id)
        waiting = QueueTicket.objects.filter(
            service=service,
            status='waiting',
        ).order_by('joined_at')

        serving = QueueTicket.objects.filter(
            service=service,
            status='serving',
        )

        context = {
            'service': service,
            'branch': service.branch,
            'waiting_tickets': waiting,
            'serving_tickets': serving,
            'waiting_count': waiting.count(),
        }
        return render(request, 'citizen/queue_overview.html', context)


class MyTicketsView(CitizenRequiredMixin, View):
    """Citizen views all their active tickets."""

    def get(self, request):
        active_tickets = QueueTicket.objects.filter(
            citizen=request.user,
            status__in=['waiting', 'serving'],
        ).select_related('service', 'branch')

        past_tickets = QueueTicket.objects.filter(
            citizen=request.user,
            status__in=['served', 'no_show'],
        ).select_related('service', 'branch').order_by('-joined_at')[:20]

        return render(request, 'citizen/my_tickets.html', {
            'active_tickets': active_tickets,
            'past_tickets': past_tickets,
        })


class ServeNextView(OperatorRequiredMixin, View):
    """Operator serves the next citizen in FIFO order. No skipping."""

    def post(self, request):
        try:
            assignment = request.user.operator_assignment
            counter = assignment.counter
        except OperatorAssignment.DoesNotExist:
            messages.error(request, 'You are not assigned to any counter.')
            return redirect('counters:operator_dashboard')

        if not counter.is_open:
            messages.error(request, 'Your counter is closed. Open it first.')
            return redirect('counters:operator_dashboard')

        # Complete current ticket if any
        current_serving = QueueTicket.objects.filter(
            service=counter.service,
            branch=counter.branch,
            status='serving',
        ).first()

        if current_serving:
            engine.mark_served(current_serving)
            messages.info(request, f'Token #{current_serving.token_number} marked as served.')

        # Get next ticket (strict FIFO)
        ticket = engine.serve_next(counter)
        if ticket:
            messages.success(request, f'Now serving Token #{ticket.token_number}')
        else:
            messages.info(request, 'No citizens waiting in queue.')

        return redirect('counters:operator_dashboard')


class MarkNoShowView(OperatorRequiredMixin, View):
    """Mark the current ticket as no-show."""

    def post(self, request):
        try:
            assignment = request.user.operator_assignment
            counter = assignment.counter
        except OperatorAssignment.DoesNotExist:
            messages.error(request, 'You are not assigned to any counter.')
            return redirect('counters:operator_dashboard')

        ticket_id = request.POST.get('ticket_id')
        ticket = get_object_or_404(
            QueueTicket,
            id=ticket_id,
            service=counter.service,
            branch=counter.branch,
            status='serving',
        )

        engine.mark_no_show(ticket)
        messages.warning(request, f'Token #{ticket.token_number} marked as NO SHOW.')
        return redirect('counters:operator_dashboard')
