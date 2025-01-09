from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # New path for account settings
    path('account-settings/', views.account_settings, name='account_settings'),
    path('transactions/', views.transactions, name='transactions'),
]