# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('gallery/', views.gallery, name='gallery'),
    path('chefs/', views.chefs, name='chefs'),
    path('events/', views.events, name='events'),
    #path('contact/submit/', views.contact_submit, name='contact_submit'),
    path('testimonials', views.testimonials, name='testimonials'),
    path('hero', views.hero, name='hero'),
    path('stats', views.stats, name='stats'),
    path('why_us', views.why_us, name='why_us'),
]