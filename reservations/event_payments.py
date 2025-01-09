# import stripe
# from django.conf import settings
# from decimal import Decimal
#
# stripe.api_key = settings.STRIPE_SECRET_KEY
#
# def create_event_payment_intent(booking):
#     """Create payment intent for event booking"""
#     try:
#         # Convert amount to cents for Stripe
#         amount = int(booking.total_amount * Decimal('100'))
#
#         intent = stripe.PaymentIntent.create(
#             amount=amount,
#             currency='usd',
#             metadata={
#                 'booking_id': booking.id,
#                 'event_type': booking.event_type.name,
#                 'customer_email': booking.email
#             }
#         )
#         return intent
#     except Exception as e:
#         print(f"Error creating event payment intent: {e}")
#         return None
#
# def confirm_event_payment(payment_intent_id):
#     """Confirm event payment"""
#     try:
#         intent = stripe.PaymentIntent.retrieve(payment_intent_id)
#         return intent.status == 'succeeded'
#     except Exception as e:
#         print(f"Error confirming event payment: {e}")
#         return False


# reservations/event_payments.py
import stripe
from django.conf import settings
from decimal import Decimal

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_event_payment_intent(booking):
    """Create payment intent for event booking"""
    try:
        # Convert amount to cents for Stripe
        amount = int(booking.total_amount * Decimal('100'))

        # Create test payment intent
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            metadata={
                'booking_id': booking.id,
                'event_type': booking.event_type.name,
                'customer_email': booking.email,
                'environment': 'test'  # Mark as test payment
            },
            # Optional: Automatically confirm the payment for testing
            confirm=False,
            # Use test payment methods only
            payment_method_types=['card']
        )
        return intent
    except Exception as e:
        print(f"Error creating event payment intent: {e}")
        return None