"""
Queue Engine: core FIFO queue logic with ETA calculation.
No skipping. No manual selection. Strict FIFO enforcement.
"""

from django.utils import timezone
from django.db.models import Max, F
from django.conf import settings

from core.utils import calculate_eta
from .models import QueueTicket


def join_queue(citizen, service):
    """
    Add a citizen to the queue for a service. FIFO order.
    Returns the created QueueTicket.
    Raises ValueError if citizen already has an active ticket for this service.
    Raises ValueError if no counters are open for this service.
    """
    from counters.models import Counter

    # Check for existing active ticket
    existing = QueueTicket.objects.filter(
        citizen=citizen,
        service=service,
        status__in=['waiting', 'serving'],
    ).exists()
    if existing:
        raise ValueError('You already have an active ticket for this service.')

    # Check that at least one counter is open
    open_counters = Counter.objects.filter(service=service, is_open=True).count()
    if open_counters == 0:
        raise ValueError('No counters are currently open for this service. Please try again later.')

    # Generate token number: max token for this branch today + 1
    today = timezone.localdate()
    max_token = QueueTicket.objects.filter(
        branch=service.branch,
        joined_at__date=today,
    ).aggregate(max_token=Max('token_number'))['max_token'] or 0
    token_number = max_token + 1

    # Calculate position: count of waiting tickets ahead + 1
    position = QueueTicket.objects.filter(
        service=service,
        status='waiting',
    ).count() + 1

    # Calculate ETA
    active_counters = open_counters
    eta = calculate_eta(position, service.avg_service_time, active_counters)

    ticket = QueueTicket.objects.create(
        citizen=citizen,
        service=service,
        branch=service.branch,
        token_number=token_number,
        status='waiting',
        position=position,
        estimated_wait_time=eta,
    )

    return ticket


def serve_next(counter):
    """
    Get the next WAITING ticket for the counter's service (strict FIFO).
    Marks it as SERVING with called_at timestamp.
    Returns the ticket or None if queue is empty.
    """
    # Get the earliest waiting ticket for this service (FIFO)
    ticket = QueueTicket.objects.filter(
        service=counter.service,
        branch=counter.branch,
        status='waiting',
    ).order_by('joined_at').first()

    if ticket is None:
        return None

    ticket.status = 'serving'
    ticket.called_at = timezone.now()
    ticket.save()

    # Check and send turn alerts for upcoming tickets
    _check_turn_alerts(counter.service)

    return ticket


def mark_served(ticket):
    """Mark a ticket as served and update service avg time."""
    ticket.status = 'served'
    ticket.served_at = timezone.now()
    ticket.save()

    # Update average service time
    if ticket.called_at:
        service_duration = (ticket.served_at - ticket.called_at).total_seconds() / 60
        service = ticket.service
        # Simple rolling average
        current_avg = service.avg_service_time
        service.avg_service_time = int((current_avg + service_duration) / 2)
        service.save()

    # Recalculate positions and ETAs
    recalculate_eta(ticket.service)


def mark_no_show(ticket):
    """Mark a ticket as no-show and advance the queue."""
    ticket.status = 'no_show'
    ticket.no_show_at = timezone.now()
    ticket.save()

    # Recalculate positions and ETAs for remaining tickets
    recalculate_eta(ticket.service)


def recalculate_eta(service):
    """
    Recalculate ETA for all waiting tickets in a service.
    Called when: counter opens/closes, ticket served, ticket no-show.
    ETA = (position * avg_service_time) / active_counters
    """
    from counters.models import Counter

    active_counters = Counter.objects.filter(
        service=service,
        is_open=True,
    ).count()

    waiting_tickets = QueueTicket.objects.filter(
        service=service,
        status='waiting',
    ).order_by('joined_at')

    for idx, ticket in enumerate(waiting_tickets, start=1):
        ticket.position = idx
        ticket.estimated_wait_time = calculate_eta(
            idx, service.avg_service_time, active_counters
        )
        ticket.save(update_fields=['position', 'estimated_wait_time'])

    # After recalculating, check for turn alerts
    _check_turn_alerts(service)


def _check_turn_alerts(service):
    """Send turn alerts for tickets with ETA <= threshold."""
    threshold = getattr(settings, 'TURN_ALERT_THRESHOLD_MINUTES', 5)

    tickets_to_alert = QueueTicket.objects.filter(
        service=service,
        status='waiting',
        estimated_wait_time__lte=threshold,
        estimated_wait_time__gt=0,
    )

    for ticket in tickets_to_alert:
        from notifications.services import send_turn_alert
        send_turn_alert(ticket)
