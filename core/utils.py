"""
Shared utility functions.
"""

import random
import math
from django.conf import settings


def generate_otp():
    """Generate a random numeric OTP of configured length."""
    length = getattr(settings, 'OTP_LENGTH', 6)
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])


def calculate_eta(position, avg_service_time_minutes, active_counter_count):
    """
    Calculate estimated wait time in minutes.

    ETA = (position * avg_service_time) / active_counters

    Args:
        position: Position in queue (1-based)
        avg_service_time_minutes: Average service time in minutes
        active_counter_count: Number of open counters for this service

    Returns:
        Estimated wait time in minutes (integer, rounded up)
    """
    if active_counter_count <= 0:
        return -1  # Cannot estimate when no counters are open

    if position <= 0:
        return 0

    eta = (position * avg_service_time_minutes) / active_counter_count
    return max(1, math.ceil(eta))
