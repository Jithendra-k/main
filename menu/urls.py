# menu/urls.py
from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    path('', views.menu_list, name='menu_list'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
]