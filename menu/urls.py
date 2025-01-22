# menu/urls.py
from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    path('', views.menu_list, name='menu_list'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    # Add to cart with customizations
    path('add-to-cart/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    # Calculate price based on selected options
    path('item/<int:item_id>/price/', views.get_item_price, name='get_item_price'),
    # Get customization options for an item
    path('item/<int:item_id>/customizations/', views.get_customization_options, name='get_customization_options'),
    # Get menu items (for dynamic loading/filtering)
    path('items/', views.get_menu_items, name='get_menu_items'),
]