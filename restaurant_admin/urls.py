from django.urls import path
from . import views

app_name = 'restaurant_admin'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('update-store-status/', views.update_store_status, name='update_store_status'),

    #Manage Orders
    path('order/<int:order_id>/', views.order_details, name='order_details'),
    path('order/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    path('order-stats/', views.order_stats, name='order_stats'),
    path('order-stats/export-pdf/', views.export_order_stats_pdf, name='export_order_stats_pdf'),
    path('store-chart-data/', views.store_chart_data, name='store_chart_data'),

    #Manage Reservations
    path('reservation/<int:reservation_id>/update-status/', views.update_reservation_status, name='update_reservation_status'),
    path('reservation/<int:reservation_id>/update-arrival-status/', views.update_arrival_status, name='update_arrival_status'),
    # path('reservations/', views.reservations_by_date, name='reservations_by_date'),
    path('reservations/', views.get_reservations, name='get_reservations'),
    path('reservation/<int:reservation_id>/', views.reservation_details, name='reservation_details'),
    path('add-reservation/', views.add_manual_reservation, name='add_manual_reservation'),

    # Menu Management URLs
    path('menu/', views.food_menu, name='food_menu'),

    # Category Management
    path('menu/category/add/', views.add_category, name='add_category'),
    path('menu/category/<int:category_id>/edit/', views.edit_category, name='edit_category'),
    path('menu/category/<int:category_id>/delete/', views.delete_category, name='delete_category'),

    # Menu Item Management
    path('menu/item/add/', views.add_menu_item, name='add_menu_item'),
    path('menu/item/<int:item_id>/get/', views.get_menu_item, name='get_menu_item'),
    path('menu/item/<int:item_id>/edit/', views.edit_menu_item, name='edit_menu_item'),
    path('menu/item/<int:item_id>/delete/', views.delete_menu_item, name='delete_menu_item'),
    path('menu/item/<int:item_id>/toggle/', views.toggle_menu_item, name='toggle_menu_item'),

    # Choice Management
    path('menu/choice/add/', views.add_choice, name='add_choice'),
    path('menu/choice/<int:choice_id>/get/', views.get_choice, name='get_choice'),
    path('menu/choice/<int:choice_id>/edit/', views.edit_choice, name='edit_choice'),
    path('menu/choice/<int:choice_id>/delete/', views.delete_choice, name='delete_choice'),

    # Add-on Management
    path('menu/addon/add/', views.add_addon, name='add_addon'),
    path('menu/addon/<int:addon_id>/get/', views.get_addon, name='get_addon'),
    path('menu/addon/<int:addon_id>/edit/', views.edit_addon, name='edit_addon'),
    path('menu/addon/<int:addon_id>/delete/', views.delete_addon, name='delete_addon'),

    #customer management
    path('customers/', views.customer_management, name='customer_management'),
    path('customers/<int:user_id>', views.customer_detail, name='customer_detail'),

    #Manage Giftcards
    path('giftcards/', views.manage_giftcards, name='manage_giftcards'),
    path('giftcards/validate/', views.validate_giftcard, name='validate_giftcard'),
    path('giftcards/redeem/', views.redeem_giftcard, name='redeem_giftcard'),

    #Manage Payments
    path('payments/', views.manage_payments, name='manage_payments'),
    path('transaction/<int:transaction_id>/', views.get_transaction_details, name='get_transaction_details'),
    path('transaction/<int:transaction_id>/refund/', views.process_refund, name='process_refund'),
    path('customer/<int:user_id>/transactions/', views.customer_transactions, name='customer_transactions'),
    path('transactions/export-pdf/', views.export_transactions_pdf, name='export_transactions_pdf'),

    #Manage Settings
    path('settings/', views.settings, name='settings'),
    path('settings/update-account/', views.update_account, name='update_account'),
    path('settings/announcement/add/', views.add_announcement, name='add_announcement'),
    path('settings/announcement/<int:announcement_id>/', views.edit_announcement, name='edit_announcement'),
    path('settings/announcement/<int:announcement_id>/edit/', views.edit_announcement, name='edit_announcement'),
    path('settings/announcement/<int:announcement_id>/delete/', views.delete_announcement, name='delete_announcement'),

]