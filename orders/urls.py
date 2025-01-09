# orders/urls.py
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Cart and Order Management
    path('cart/', views.cart_detail, name='cart_detail'),
    path('save-cart/', views.save_cart, name='save_cart'),
    path('get-cart/', views.get_cart, name='get_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('check-store-status/', views.check_store_status, name='check_store_status'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order-detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('repeat-order/<int:order_id>/', views.repeat_order, name='repeat_order'),

    # Regular Card Payment
    path('create-payment-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-cancel/<int:order_id>/', views.payment_cancel, name='payment_cancel'),


    # PayPal Integration
    path('create-paypal-order/', views.create_paypal_order, name='create_paypal_order'),
    path('capture-paypal-payment/', views.capture_paypal_payment, name='capture_paypal_payment'),
    path('paypal-success/', views.paypal_success, name='paypal_success'),
    path('paypal-cancel/', views.paypal_cancel, name='paypal_cancel'),

    # Apple Pay Integration
    path('validate-apple-pay/', views.validate_apple_pay, name='validate_apple_pay'),
    path('process-apple-pay/', views.process_apple_pay, name='process_apple_pay'),
    path('apple-pay-success/', views.apple_pay_success, name='apple_pay_success'),
    path('apple-pay-cancel/', views.apple_pay_cancel, name='apple_pay_cancel'),
]