# reservations/urls.py
from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    # Existing URLs
    path('book-table/', views.book_table, name='book_table'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
    path('confirm-reservation/<int:reservation_id>/', views.confirm_reservation, name='confirm_reservation'),
    path('update-reservation/<int:reservation_id>/', views.update_reservation, name='update_reservation'),
    path('cancel-reservation/<int:reservation_id>/', views.cancel_reservation, name='cancel_reservation'),

    # Event booking URLs
    path('book-event/', views.book_event, name='book_event'),
    path('event-payment/<int:booking_id>/', views.event_payment, name='event_payment'),
    path('process-event-payment/<int:booking_id>/', views.process_event_payment, name='process_event_payment'),
    path('payment-success/<int:booking_id>/', views.payment_success, name='payment_success'),
    path('payment-cancel/<int:booking_id>/', views.payment_cancel, name='payment_cancel'),

    path('clear-messages/', views.clear_messages, name='clear_messages'),

]