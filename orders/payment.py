# orders/payment.py
import stripe
from django.conf import settings
from decimal import Decimal

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_payment_intent(order):
    try:
        # Convert amount to cents
        amount = int(order.total_amount * Decimal('100'))

        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            metadata={
                'order_id': order.id,
                'customer_email': order.email
            }
        )
        return intent
    except Exception as e:
        print(f"Error creating payment intent: {e}")
        return None


def confirm_payment(payment_intent_id):
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return intent.status == 'succeeded'
    except Exception as e:
        print(f"Error confirming payment: {e}")
        return False