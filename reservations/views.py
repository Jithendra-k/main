# reservations/views.py
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.html import strip_tags

from .models import Reservation, EventBooking, EventType
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# reservations/views.py

from orders.payment import create_payment_intent, confirm_payment
from orders.payment_methods import PayPalClient, ApplePayClient
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages


@require_http_methods(["POST"])
def clear_messages(request):
    """Clear all messages and related session data."""
    # Clear Django messages
    storage = messages.get_messages(request)
    for _ in storage:
        pass
    storage.used = True

    # Clear session
    request.session.pop('messages', None)
    request.session.pop('_messages', None)

    # Clear any other message-related session keys
    keys_to_remove = [k for k in request.session.keys() if 'message' in k.lower()]
    for key in keys_to_remove:
        request.session.pop(key, None)

    request.session.modified = True

    return JsonResponse({'status': 'success'})


# reservations/views.py
@login_required
def book_table(request):
    storage = messages.get_messages(request)
    storage.used = True
    request.session.pop('messages', None)

    if request.method == 'POST':
        try:
            # Basic validation
            required_fields = ['name', 'email', 'phone', 'date', 'time', 'guests']
            for field in required_fields:
                if not request.POST.get(field):
                    raise ValueError(f'{field.capitalize()} is required')

            # Parse date and time
            date_str = request.POST['date']
            time_str = request.POST['time']

            try:
                # Convert to proper date and time objects
                booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                booking_time = datetime.strptime(time_str, '%H:%M').time()

                # Create aware datetime for validation
                booking_datetime = timezone.make_aware(
                    datetime.combine(booking_date, booking_time)
                )

                if booking_datetime <= timezone.now():
                    raise ValueError('Please select a future date and time')

                if booking_time.hour < 12 or booking_time.hour >= 21:
                    raise ValueError('Bookings are only available between 12:00 PM and 9:00 PM')

            except ValueError as e:
                messages.error(request, str(e))
                return render(request, 'reservations/book_table.html', status=400)

            # Create reservation with pending status
            reservation = Reservation.objects.create(
                user=request.user,
                name=request.POST['name'],
                email=request.POST['email'],
                phone=request.POST['phone'],
                date=booking_date,  # Use the datetime object
                time=booking_time,  # Use the time object
                guests=int(request.POST['guests']),
                special_request=request.POST.get('special_request', ''),
                status='pending'
            )
            try:
                # After successful reservation creation
                notify_admin("new_reservation", {
                    "id": reservation.id,
                    "time": reservation.time.strftime("%H:%M"),
                    "name": reservation.name,
                    "guests": reservation.guests,
                    "status": reservation.get_status_display()
                })
            except Exception as e:
                print(f"Error sending notification to admin -websocket: {e}")

            # Send notification to restaurant
            send_reservation_request_to_restaurant(reservation)

            messages.success(request,
                             'Your table reservation request has been submitted successfully! You will receive a confirmation email once approved.')
            return render(request, 'reservations/reservation_pending.html', {
                'reservation': reservation
            })

        except Exception as e:
            print(f"Error in book_table: {str(e)}")  # Debug print
            messages.error(request, 'An error occurred while processing your reservation. Please try again.')
            return render(request, 'reservations/book_table.html', status=500)

    return render(request, 'reservations/book_table.html')

def send_reservation_request_to_restaurant(reservation):
    """Send notification to restaurant about new reservation request"""
    try:
        # Convert string date/time to datetime objects if needed
        if isinstance(reservation.date, str):
            date_obj = datetime.strptime(reservation.date, '%Y-%m-%d')
        else:
            date_obj = reservation.date

        if isinstance(reservation.time, str):
            time_obj = datetime.strptime(reservation.time, '%H:%M').time()
        else:
            time_obj = reservation.time

        subject = f'New Table Reservation Request - #{reservation.id}'
        context = {
            'reservation': reservation,
            'formatted_date': date_obj.strftime("%B %d, %Y"),
            'formatted_time': time_obj.strftime("%I:%M %p")
        }

        html_message = render_to_string(
            'reservations/emails/restaurant_reservation_request.html',
            context
        )
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email='jithendrakatta9999@gmail.com',
            recipient_list=[settings.RESTAURANT_ORDER_EMAIL],
            fail_silently=False,
        )
        print(f"Restaurant notification sent for reservation #{reservation.id}")
    except Exception as e:
        print(f"Error sending restaurant notification: {str(e)}")
        print("Date type:", type(reservation.date))
        print("Time type:", type(reservation.time))


@login_required
def confirm_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    return render(request, 'reservations/confirm_reservation.html', {
        'reservation': reservation
    })


# In reservations/views.py
@login_required
def book_event(request):
    # Clear any existing messages at the start
    if request.method == 'GET':
        storage = messages.get_messages(request)
        for _ in storage:
            pass  # Iterate through to mark all as used
        storage.used = True

        # Also clear session
        request.session['messages'] = []
        request.session.modified = True

        event_types = EventType.objects.all().order_by('base_price')
        return render(request, 'reservations/book_event.html', {
            'event_types': event_types
        })

    event_types = EventType.objects.all().order_by('base_price')

    if request.method == 'POST':
        try:
            # Validate event type
            event_type = get_object_or_404(EventType, id=request.POST['event_type'])

            # Validate date and time
            date_str = request.POST['date']
            time_str = request.POST['time']

            try:
                booking_datetime = timezone.make_aware(
                    datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                )

                # Validate booking is in future
                if booking_datetime <= timezone.now():
                    messages.error(request, 'Please select a future date and time.')
                    return redirect('reservations:book_event')

                # Validate time is within business hours (11 AM - 11 PM)
                hour = booking_datetime.hour
                if hour < 12 or hour >= 21:
                    messages.error(request, 'Events can only be booked between 12:00 PM and 09:00 PM')
                    return redirect('reservations:book_event')

            except ValueError:
                messages.error(request, 'Invalid date or time format')
                return redirect('reservations:book_event')

            # Validate number of guests
            guests = int(request.POST['guests'])
            if guests > event_type.max_capacity:
                messages.error(request,
                               f'Maximum capacity for this event is {event_type.max_capacity} guests.')
                return redirect('reservations:book_event')

            if guests <= 0:
                messages.error(request, 'Number of guests must be greater than 0.')
                return redirect('reservations:book_event')

            # Calculate total amount using Decimal
            base_price = event_type.base_price
            guest_factor = Decimal(str(1 + (guests / 100)))  # Convert to Decimal
            total_amount = base_price * guest_factor

            # Create event booking
            booking = EventBooking.objects.create(
                user=request.user,
                event_type=event_type,
                name=request.POST['name'],
                email=request.POST['email'],
                phone=request.POST['phone'],
                date=date_str,
                time=time_str,
                guests=guests,
                special_request=request.POST.get('special_request', ''),
                total_amount=total_amount,
                status='pending',
                payment_status='pending'
            )

            # Redirect to payment
            messages.success(request, 'Event booking created successfully. Please complete the payment.')
            return redirect('reservations:event_payment', booking_id=booking.id)

        except Exception as e:
            messages.error(request, f'Error processing event booking: {str(e)}')
            return redirect('reservations:book_event')

    # For GET request, render the booking form
    return render(request, 'reservations/book_event.html', {
        'event_types': event_types
    })


@login_required
def my_reservations(request):
    # Get table reservations and event bookings
    table_reservations_list = Reservation.objects.filter(user=request.user).order_by('-date', '-time')
    event_bookings_list = EventBooking.objects.filter(user=request.user).order_by('-date', '-time')

    # Set up pagination for table reservations
    table_paginator = Paginator(table_reservations_list, 10)
    table_page = request.GET.get('table_page')

    try:
        table_reservations = table_paginator.page(table_page)
    except PageNotAnInteger:
        table_reservations = table_paginator.page(1)
    except EmptyPage:
        table_reservations = table_paginator.page(table_paginator.num_pages)

    # Set up pagination for event bookings
    event_paginator = Paginator(event_bookings_list, 10)
    event_page = request.GET.get('event_page')

    try:
        event_bookings = event_paginator.page(event_page)
    except PageNotAnInteger:
        event_bookings = event_paginator.page(1)
    except EmptyPage:
        event_bookings = event_paginator.page(event_paginator.num_pages)

    # Add parameters for cross-referencing paginations
    table_page_param = f'table_page={table_reservations.number}' if table_reservations else ''
    event_page_param = f'event_page={event_bookings.number}' if event_bookings else ''

    return render(request, 'reservations/my_reservations.html', {
        'table_reservations': table_reservations,
        'event_bookings': event_bookings,
        'now': timezone.now(),
        'table_page_param': table_page_param,
        'event_page_param': event_page_param
})


@login_required
def update_reservation(request, reservation_id):
    try:
        # Try to get table reservation first
        reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
        is_event = False
        if not reservation.can_modify():
            messages.error(request, 'Table reservations can only be modified up to 3 hours before the scheduled time.')
            return redirect('reservations:my_reservations')
    except:
        # If not found, try event booking
        reservation = get_object_or_404(EventBooking, id=reservation_id, user=request.user)
        is_event = True
        if not reservation.can_modify():
            messages.error(request, 'Event bookings can only be modified up to 3 hours before the scheduled time.')
            return redirect('reservations:my_reservations')

    if request.method == 'POST':
        try:
            # Convert date and time strings to datetime objects for validation
            date_str = request.POST['date']
            time_str = request.POST['time']
            booking_datetime = timezone.make_aware(
                datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            )

            # Validate booking time is in the future
            if booking_datetime <= timezone.now():
                messages.error(request, 'Please select a future date and time.')
                return redirect('reservations:my_reservations')

            # Update the reservation
            reservation.date = date_str
            reservation.time = time_str
            reservation.guests = request.POST['guests']
            reservation.special_request = request.POST.get('special_request', '')

            if is_event:
                # Additional validation for events
                if int(request.POST['guests']) > reservation.event_type.max_capacity:
                    messages.error(request,
                                   f'Maximum capacity for this event is {reservation.event_type.max_capacity} guests.')
                    return redirect('reservations:my_reservations')

            reservation.save()

            # Send update email
            send_reservation_update(reservation)

            messages.success(request, f'{"Event" if is_event else "Table"} reservation updated successfully!')
            return redirect('reservations:my_reservations')

        except Exception as e:
            messages.error(request, f'Error updating reservation: {str(e)}')
            return redirect('reservations:my_reservations')

    context = {
        'reservation': reservation,
        'is_event': is_event,
        'min_date': timezone.now().date().strftime('%Y-%m-%d')
    }
    return render(request, 'reservations/update_reservation.html', context)





@login_required
def event_payment(request, booking_id):
    booking = get_object_or_404(EventBooking, id=booking_id, user=request.user)

    if booking.payment_status == 'paid':
        messages.warning(request, 'This event has already been paid for.')
        return redirect('reservations:my_reservations')

    # Create payment intent using the new function
    from .event_payments import create_event_payment_intent
    intent = create_event_payment_intent(booking)

    if not intent:
        messages.error(request, 'Error creating payment. Please try again.')
        return redirect('reservations:my_reservations')

    context = {
        'booking': booking,
        'client_secret': intent.client_secret,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'paypal_client_id': settings.PAYPAL_CLIENT_ID
    }
    return render(request, 'reservations/event_payment.html', context)


@login_required
def process_event_payment(request, booking_id):
    booking = get_object_or_404(EventBooking, id=booking_id, user=request.user)
    data = json.loads(request.body)
    payment_method = data.get('payment_method')

    try:
        if payment_method == 'stripe':
            from .event_payments import confirm_event_payment
            payment_intent_id = data.get('payment_intent_id')
            success = confirm_event_payment(payment_intent_id)

            if success:
                # Update booking status
                booking.payment_status = 'paid'
                booking.status = 'confirmed'
                booking.save()

                # Send confirmation emails
                try:
                    # Email to customer
                    send_event_booking_confirmation(booking)

                    # Email to restaurant
                    send_event_booking_notification_to_restaurant(booking)

                    return JsonResponse(
                        {'status': 'success', 'message': 'Payment successful and confirmation emails sent'})
                except Exception as e:
                    print(f"Error sending confirmation emails: {e}")
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Payment successful but there was an error sending confirmation emails'
                    })
            else:
                return JsonResponse({'error': 'Payment failed'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def send_event_booking_confirmation(booking):
    """Send confirmation email to customer"""
    subject = f'Event Booking Confirmation - {booking.event_type.name}'
    context = {
        'booking': booking,
        'formatted_date': booking.date.strftime("%B %d, %Y"),
        'formatted_time': booking.time.strftime("%I:%M %p"),
    }

    html_message = render_to_string(
        'reservations/emails/event_confirmation.html',
        context
    )
    plain_message = strip_tags(html_message)

    send_mail(
        subject=subject,
        message=plain_message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[booking.email],
        fail_silently=False,
    )


def send_event_booking_notification_to_restaurant(booking):
    """Send notification email to restaurant"""
    subject = f'New Event Booking - {booking.event_type.name}'
    context = {
        'booking': booking,
        'formatted_date': booking.date.strftime("%B %d, %Y"),
        'formatted_time': booking.time.strftime("%I:%M %p"),
    }

    html_message = render_to_string(
        'reservations/emails/event_notification.html',
        context
    )
    plain_message = strip_tags(html_message)

    send_mail(
        subject=subject,
        message=plain_message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.RESTAURANT_ORDER_EMAIL],
        fail_silently=False,
    )


@login_required
def payment_success(request, booking_id):
    booking = get_object_or_404(EventBooking, id=booking_id, user=request.user)
    messages.success(request, 'Payment successful! Your event booking has been confirmed.')
    return redirect('reservations:my_reservations')


@login_required
def payment_cancel(request, booking_id):
    messages.warning(request, 'Payment was cancelled. Your booking is still pending.')
    return redirect('reservations:my_reservations')


# In reservations/views.py
def send_reservation_confirmation(reservation):
    """Send reservation confirmation email to customer"""
    subject = 'Table Reservation Confirmation - Royal Nepal Restaurant'

    try:
        # Convert string date/time to datetime objects if needed
        if isinstance(reservation.date, str):
            date_obj = datetime.strptime(reservation.date, '%Y-%m-%d')
        else:
            date_obj = reservation.date

        if isinstance(reservation.time, str):
            time_obj = datetime.strptime(reservation.time, '%H:%M').time()
        else:
            time_obj = reservation.time

        context = {
            'reservation': reservation,
            'formatted_date': date_obj.strftime("%B %d, %Y"),
            'formatted_time': time_obj.strftime("%I:%M %p")
        }

        html_message = render_to_string(
            'reservations/emails/reservation_confirmation.html',
            context
        )
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[reservation.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending confirmation email: {e}")


def send_reservation_update(reservation):
    """Send update confirmation email"""
    subject = 'Reservation Update Confirmation - Royal Nepal Restaurant'

    try:
        # Convert string date/time to datetime objects if needed
        if isinstance(reservation.date, str):
            date_obj = datetime.strptime(reservation.date, '%Y-%m-%d')
        else:
            date_obj = reservation.date

        if isinstance(reservation.time, str):
            time_obj = datetime.strptime(reservation.time, '%H:%M').time()
        else:
            time_obj = reservation.time

        context = {
            'reservation': reservation,
            'formatted_date': date_obj.strftime("%B %d, %Y"),
            'formatted_time': time_obj.strftime("%I:%M %p")
        }

        html_message = render_to_string(
            'reservations/emails/reservation_update.html',
            context
        )
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[reservation.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending update email: {e}")


# In reservations/views.py

@login_required
def cancel_reservation(request, reservation_id):
    try:
        # Try to get table reservation first
        reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
        is_event = False

        if not reservation.can_modify():
            messages.error(request, 'Table reservations can only be cancelled up to 3 hours before the scheduled time.')
            return redirect('reservations:my_reservations')

        if request.method == 'POST':
            reservation.status = 'cancelled'
            reservation.save()

            # Send cancellation email
            send_cancellation_email(reservation)

            messages.success(request, 'Table reservation cancelled successfully.')
            return redirect('reservations:my_reservations')

    except Reservation.DoesNotExist:
        # If not found, try event booking
        try:
            booking = get_object_or_404(EventBooking, id=reservation_id, user=request.user)
            is_event = True

            if not booking.can_modify():
                messages.error(request,
                               'Event bookings cannot be cancelled less than 3 hours before the scheduled time.')
                return redirect('reservations:my_reservations')

            if request.method == 'POST':
                booking_time = timezone.make_aware(datetime.combine(booking.date, booking.time))
                time_until_event = booking_time - timezone.now()

                # Calculate refund amount
                if time_until_event > timedelta(hours=24):
                    refund_amount = booking.total_amount
                    refund_percentage = 100
                elif time_until_event > timedelta(hours=3):
                    refund_amount = booking.total_amount * Decimal('0.25')
                    refund_percentage = 25
                else:
                    refund_amount = Decimal('0')
                    refund_percentage = 0

                booking.status = 'cancelled'
                booking.save()

                # Send cancellation email with refund info
                send_cancellation_email(booking, is_event=True,
                                        refund_amount=refund_amount,
                                        refund_percentage=refund_percentage)

                if refund_amount > 0:
                    messages.success(request,
                                     f'Event booking cancelled successfully. {refund_percentage}% refund (${refund_amount}) will be processed.')
                else:
                    messages.success(request, 'Event booking cancelled successfully. No refund is applicable.')

                return redirect('reservations:my_reservations')

            return render(request, 'reservations/cancel_reservation.html', {
                'booking': booking,
                'is_event': True
            })

        except EventBooking.DoesNotExist:
            messages.error(request, 'Reservation not found.')
            return redirect('reservations:my_reservations')

    return render(request, 'reservations/cancel_reservation.html', {
        'reservation': reservation,
        'is_event': False
    })


def send_cancellation_email(reservation, is_event=False, refund_amount=0, refund_percentage=0):
    """Send cancellation confirmation email"""
    subject = 'Reservation Cancellation Confirmation - Royal Nepal Restaurant'

    try:
        # Convert date/time to proper format
        if isinstance(reservation.date, str):
            date_obj = datetime.strptime(reservation.date, '%Y-%m-%d')
        else:
            date_obj = reservation.date

        if isinstance(reservation.time, str):
            time_obj = datetime.strptime(reservation.time, '%H:%M').time()
        else:
            time_obj = reservation.time

        context = {
            'reservation': reservation,
            'formatted_date': date_obj.strftime("%B %d, %Y"),
            'formatted_time': time_obj.strftime("%I:%M %p"),
            'is_event': is_event,
            'refund_amount': refund_amount,
            'refund_percentage': refund_percentage,
            'restaurant_name': 'Royal Nepal',
            'restaurant_contact': '+1 5589 55488 55'
        }

        html_message = render_to_string(
            'reservations/emails/reservation_cancellation.html',
            context
        )
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[reservation.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending cancellation email: {e}")
        # Log the error but don't stop the cancellation process

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def notify_admin(notification_type, data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "admin_notifications",
        {
            "type": "notification_message",
            "message": {
                "type": notification_type,
                "data": data
            }
        }
    )




