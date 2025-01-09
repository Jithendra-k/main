# reservations/models.py
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# Keep EventType model unchanged
class EventType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_capacity = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),  # Added new status
        ('cancelled', 'Cancelled')
    ]

    ARRIVAL_STATUS_CHOICES = [
        ('not_arrived', 'Not yet Arrived'),
        ('seated', 'Seated'),
        ('no_show', 'No Show')
    ]



    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    date = models.DateField()
    time = models.TimeField()
    guests = models.PositiveIntegerField()
    special_request = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    arrival_status = models.CharField(
        max_length=20,
        choices=ARRIVAL_STATUS_CHOICES,
        default='not_arrived'
    )
    is_manual_entry = models.BooleanField(default=False)  # New field for staff-created reservations
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'time']  # Changed to ascending order for dashboard display

    def __str__(self):
        return f"Reservation for {self.name} on {self.date} at {self.time}"

    def get_formatted_date(self):
        return self.date.strftime('%B %d, %Y')

    def get_formatted_time(self):
        return self.time.strftime('%I:%M %p')

    def can_modify(self):
        # Keep existing modification check
        reservation_datetime = timezone.make_aware(
            timezone.datetime.combine(self.date, self.time)
        )
        return timezone.now() <= (reservation_datetime - timedelta(hours=3))

# Keep EventBooking model unchanged
class EventBooking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_bookings')
    event_type = models.ForeignKey(EventType, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    date = models.DateField()
    time = models.TimeField()
    guests = models.PositiveIntegerField()
    special_request = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('paid', 'Paid')],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Event Booking: {self.event_type.name} for {self.name} on {self.date}"

    def calculate_total(self):
        return self.event_type.base_price

    def can_modify(self):
        event_datetime = timezone.make_aware(
            timezone.datetime.combine(self.date, self.time)
        )
        return timezone.now() <= (event_datetime - timedelta(hours=3))

    def get_refund_amount(self):
        event_datetime = timezone.make_aware(
            timezone.datetime.combine(self.date, self.time)
        )
        time_until_event = event_datetime - timezone.now()

        if time_until_event > timedelta(hours=24):
            return self.total_amount
        elif time_until_event > timedelta(hours=3):
            return self.total_amount * Decimal('0.25')
        return Decimal('0')

    def get_refund_policy_display(self):
        event_datetime = timezone.make_aware(
            timezone.datetime.combine(self.date, self.time)
        )
        time_until_event = event_datetime - timezone.now()

        if time_until_event > timedelta(hours=24):
            return "Full refund available"
        elif time_until_event > timedelta(hours=3):
            return "25% refund available"
        return "No refund available"