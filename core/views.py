# core/views.py
from datetime import timezone

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
import json
from django.http import JsonResponse
from django.utils import timezone

from restaurant_admin.models import Announcement


def home(request):
    # Get the current active announcement
    now = timezone.now()
    announcement = Announcement.objects.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    ).order_by('-created_at').first()

    context = {
        'announcement': announcement,
    }
    return render(request, 'core/index.html', context)

def about(request):
    return render(request, 'core/sections/about.html')


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        try:
            # Email body
            email_message = f"""
            New Contact Form Submission

            Name: {name}
            Email: {email}
            Subject: {subject}
            Message: {message}
            """

            # Send email
            send_mail(
                subject=f'Contact Form: {subject}',
                message=email_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=False,
            )

            # Send confirmation email to user
            confirmation_message = f"""
            Dear {name},

            Thank you for contacting Royal Nepal Restaurant. We have received your message and will get back to you shortly.

            Best regards,
            Royal Nepal Restaurant Team
            """

            send_mail(
                subject='Thank you for contacting Royal Nepal Restaurant',
                message=confirmation_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            # Return success response
            return JsonResponse({
                'status': 'success',
                'message': 'Your message has been sent successfully! We will contact you soon.'
            })

        except Exception as e:
            # Return error response
            return JsonResponse({
                'status': 'error',
                'message': 'Sorry, there was an error sending your message. Please try again.'
            })
    return render(request, 'core/sections/contact.html')

def gallery(request):
    return render(request, 'core/sections/gallery.html')

def chefs(request):
    return render(request, 'core/sections/chefs.html')

def events(request):
    return render(request, 'core/sections/events.html')

def testimonials(request):
    return render(request, 'core/sections/testimonials.html')

def hero(request):
    return render(request, 'core/sections/hero.html')

def stats(request):
    return render(request, 'core/sections/stats.html')

def why_us(request):
    return render(request, 'core/sections/why_us.html')


