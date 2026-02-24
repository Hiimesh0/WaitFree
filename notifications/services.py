"""
Notification services: OTP generation/verification, turn alerts, retry logic.
All notifications are logged to NotificationLog.
"""

from django.conf import settings
from django.core.cache import cache

from core.utils import generate_otp
from .models import NotificationLog


def generate_and_store_otp(mobile_number):
    """
    Generate a random OTP, store in Redis with TTL, and log it.
    Returns the OTP string.
    """
    otp = generate_otp()
    cache_key = f'otp:{mobile_number}'
    timeout = getattr(settings, 'OTP_EXPIRY_SECONDS', 300)
    cache.set(cache_key, otp, timeout=timeout)

    # Log the notification
    NotificationLog.objects.create(
        recipient_mobile=mobile_number,
        notification_type='otp',
        message=f'Your WaitFree OTP is: {otp}',
        status='sent',
    )

    return otp


def verify_otp(mobile_number, otp_entered):
    """
    Verify OTP against Redis store.
    Returns True if valid, False otherwise.
    """
    cache_key = f'otp:{mobile_number}'
    stored_otp = cache.get(cache_key)

    if stored_otp is None:
        return False

    if str(stored_otp) != str(otp_entered):
        return False

    # Delete OTP after successful verification
    cache.delete(cache_key)
    return True


def send_turn_alert(ticket):
    """
    Send a turn alert notification to a citizen when their ETA <= threshold.
    Prevents duplicate alerts for the same ticket.
    """
    # Check if alert already sent for this ticket
    existing = NotificationLog.objects.filter(
        recipient=ticket.citizen,
        notification_type='turn_alert',
        message__contains=f'Token #{ticket.token_number}',
    ).exists()

    if existing:
        return  # Don't send duplicate alerts

    mobile = ticket.citizen.mobile_number or 'N/A'
    message = (
        f'Your turn is approaching! Token #{ticket.token_number} for '
        f'{ticket.service.name}. Estimated wait: {ticket.estimated_wait_time} minutes.'
    )

    try:
        # In production, this would send an SMS/push notification
        NotificationLog.objects.create(
            recipient=ticket.citizen,
            recipient_mobile=mobile,
            notification_type='turn_alert',
            message=message,
            status='sent',
        )
    except Exception:
        log = NotificationLog.objects.create(
            recipient=ticket.citizen,
            recipient_mobile=mobile,
            notification_type='turn_alert',
            message=message,
            status='failed',
        )
        retry_notification(log.id)


def retry_notification(log_id, max_retries=3):
    """Retry a failed notification up to max_retries times."""
    try:
        log = NotificationLog.objects.get(id=log_id)
    except NotificationLog.DoesNotExist:
        return

    if log.retries >= max_retries:
        return

    log.retries += 1
    try:
        # In production: actually resend the notification
        log.status = 'retried'
        log.save()
    except Exception:
        log.status = 'failed'
        log.save()
