# main/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('menu/', include('menu.urls')),
    path('order/', include('orders.urls')),
    path('reservations/', include('reservations.urls')),
    path('giftcards/', include('giftcards.urls')),
    path('accounts/', include('accounts.urls')),  # Add this line
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='core:home'), name='logout'),
    path('register/', accounts_views.register, name='register'),
    path('restaurant-admin/', include('restaurant_admin.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)