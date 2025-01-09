from datetime import timezone
from django.utils.timezone import now
from datetime import timedelta


# In reservations/utils.py
def validate_reservation_time(booking_datetime, is_event=False):
    """
    Validate if the booking time is valid
    Returns (is_valid, error_message)
    """
    now = timezone.now()

    if booking_datetime <= now:
        return False, "Booking time must be in the future"

    # Restaurant hours (11 AM to 11 PM)
    if booking_datetime.hour < 11 or booking_datetime.hour >= 23:
        return False, "Bookings are only available between 11 AM and 11 PM"

    # Minimum advance booking
    min_hours = 24 if is_event else 3
    if booking_datetime - now < timedelta(hours=min_hours):
        return False, f"Bookings must be made at least {min_hours} hours in advance"

    return True, None