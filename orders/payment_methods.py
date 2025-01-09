# orders/payment_methods.py
import json
import requests
from django.conf import settings
from decimal import Decimal


class PayPalClient:
    def __init__(self):
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self.base_url = 'https://api-m.sandbox.paypal.com' if settings.PAYPAL_MODE == 'sandbox' else 'https://api-m.paypal.com'

    def get_access_token(self):
        auth_url = f"{self.base_url}/v1/oauth2/token"
        headers = {
            'Accept': 'application/json',
            'Accept-Language': 'en_US',
        }
        data = {
            'grant_type': 'client_credentials'
        }
        response = requests.post(auth_url,
                                 auth=(self.client_id, self.client_secret),
                                 data=data,
                                 headers=headers)
        return response.json().get('access_token')

    def create_order(self, order):
        access_token = self.get_access_token()
        url = f"{self.base_url}/v2/checkout/orders"

        payload = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "reference_id": str(order.id),
                "amount": {
                    "currency_code": "USD",
                    "value": str(order.total_amount)
                },
                "description": f"Order #{order.id} from Royal Nepal"
            }],
            "application_context": {
                "return_url": f"https://{settings.ALLOWED_HOSTS[0]}/orders/paypal-success/",
                "cancel_url": f"https://{settings.ALLOWED_HOSTS[0]}/orders/paypal-cancel/"
            }
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def capture_payment(self, order_id):
        access_token = self.get_access_token()
        url = f"{self.base_url}/v2/checkout/orders/{order_id}/capture"

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        response = requests.post(url, headers=headers)
        return response.json()


class ApplePayClient:
    def __init__(self):
        self.merchant_id = settings.APPLE_PAY_MERCHANT_ID
        self.domain = settings.APPLE_PAY_DOMAIN

    def create_payment_session(self, order):
        total_amount = float(order.total_amount)

        payment_request = {
            'countryCode': 'US',
            'currencyCode': 'USD',
            'merchantCapabilities': ['supports3DS'],
            'supportedNetworks': ['visa', 'masterCard', 'amex'],
            'total': {
                'label': 'Royal Nepal Restaurant',
                'amount': str(total_amount),
                'type': 'final'
            },
            'lineItems': [{
                'label': f'Order #{order.id}',
                'amount': str(total_amount)
            }],
            'merchantIdentifier': self.merchant_id,
            'requiredBillingContactFields': ['postalAddress', 'email'],
            'requiredShippingContactFields': ['phone'],
        }

        return payment_request

    def validate_merchant_session(self, validation_url):
        # This would be implemented with your Apple Pay certificate
        # and private key for production use
        pass

    def process_payment(self, payment_data, order):
        # Process the Apple Pay payment token
        # This would integrate with your payment processor
        # For testing, we'll simulate success
        return {
            'status': 'success',
            'transaction_id': f'AP-{order.id}-{order.created_at.timestamp()}'
        }