from django.urls import path
from . import views

app_name = 'giftcards'

urlpatterns = [
    path('', views.purchase_giftcard, name='purchase'),
    path('my-giftcards/', views.my_giftcards, name='my_giftcards'),
    path('redeem-giftcard/', views.redeem_giftcard, name='redeem_giftcard'),  # Add this line
    path('confirm-purchase/<uuid:card_id>/', views.confirm_purchase, name='confirm_purchase'),
    path('complete-payment/<uuid:card_id>/', views.complete_payment, name='complete_payment'),
    path('validate-redeem/<int:card_number>/', views.validate_redeem, name='validate_redeem'),
    path('validate/<int:card_number>/', views.validate_card, name='validate_card'),
    path('redeem/<int:card_number>/', views.redeem_card, name='redeem_card'),
]