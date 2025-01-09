import uuid
from decimal import Decimal
from django.conf import settings
import stripe
from django.db.models import Sum, Count, Case, When, Q
from django.forms import DecimalField, FloatField
from django.template import loader, RequestContext
from django.db import models
from menu.models import MenuItem, Category
from accounts.models import UserProfile, Transaction
from django.shortcuts import render, redirect, get_object_or_404
from orders.models import Order, OrderItem
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib import messages
from reservations.models import Reservation
from django.views.decorators.http import require_POST
from menu.models import Category, MenuItem
from django.core.files.storage import default_storage
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from reservations.models import Reservation
from restaurant_admin.models import StoreStatus, Announcement
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from giftcards.models import GiftCard, GiftCardTransaction
from django.db.models import Sum, Count
from datetime import timedelta
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from datetime import datetime

stripe.api_key = settings.STRIPE_SECRET_KEY



def is_staff_or_superuser(user):
    return user.is_staff or user.is_superuser


# In restaurant_admin/views.py
@user_passes_test(is_staff_or_superuser)
def dashboard(request):

    current_time = timezone.localtime(timezone.now())
    today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)


    # Get today's orders with pagination
    orders_list = Order.objects.filter(
        created_at__gte=today_start,
        created_at__lt=today_end
    ).order_by('-created_at')

    # Get today's orders with related data
    orders_list = Order.objects.filter(
        created_at__gte=today_start,
        created_at__lt=today_end
    ).select_related('user').order_by('-created_at')

    # Calculate total sales for today
    total_sales = orders_list.aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    # Total orders count
    total_orders = orders_list.count()

    paginator = Paginator(orders_list, 10)
    page = request.GET.get('order_page')

    try:
        today_orders = paginator.page(page)
    except PageNotAnInteger:
        today_orders = paginator.page(1)
    except EmptyPage:
        today_orders = paginator.page(paginator.num_pages)

    # Get today's reservations - only active ones
    reservations_list = Reservation.objects.filter(
        date=current_time.date(),
        status__in=['pending', 'confirmed'],
        arrival_status='not_arrived'
    ).order_by('time')

    # Reservations pagination
    res_paginator = Paginator(reservations_list, 10)
    res_page = request.GET.get('res_page')
    try:
        today_reservations = res_paginator.page(res_page)
    except PageNotAnInteger:
        today_reservations = res_paginator.page(1)
    except EmptyPage:
        today_reservations = res_paginator.page(res_paginator.num_pages)

    # Add page parameters for cross-referencing
    order_page_param = f'order_page={today_orders.number}' if today_orders else ''
    res_page_param = f'res_page={today_reservations.number}' if today_reservations else ''
    # Get or create store status
    store_status_obj, created = StoreStatus.objects.get_or_create(
        id=1,
        defaults={'status': 'open'}
    )
    store_status = store_status_obj.status

    context = {
        'today_orders': today_orders,
        'today_reservations': today_reservations,
        'today': current_time.date(),
        'order_page_param': order_page_param,
        'res_page_param': res_page_param,
        'store_status': store_status,
        'total_sales': total_sales,
        'total_orders': total_orders,
    }
    return render(request, 'restaurant_admin/dashboard.html', context)


@user_passes_test(is_staff_or_superuser)
def update_store_status(request):
    if request.method == 'POST':
        try:
            #print("\n=== Updating Store Status -admin===")
            data = json.loads(request.body)
            status = data.get('status')
            #print(f"Received status update request: {status}")

            if status in ['open', 'paused', 'closed']:
                status_obj, created = StoreStatus.objects.get_or_create(
                    id=1,
                    defaults={'status': 'open'}
                )
                #print(f"Previous status: {status_obj.status}")
                status_obj.status = status
                status_obj.save()
                # print(f"Status updated to: {status_obj.status}")
                # print("=== Status Update Complete -admin===\n")

                return JsonResponse({
                    'status': 'success',
                    'message': f'Store status updated to {status}',
                    'current_status': status
                })

        except Exception as e:
            print(f"Error updating store status: {str(e)}")  # For debugging
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=400)


###MANAGE ORDERS


@user_passes_test(is_staff_or_superuser)
def order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)

    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'restaurant_admin/order_details.html', context)


@user_passes_test(is_staff_or_superuser)
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')

        valid_statuses = ['pending', 'in_progress', 'ready', 'completed']
        if new_status not in valid_statuses:
            return JsonResponse({'error': 'Invalid status'}, status=400)

        order.status = new_status
        order.save()

        if new_status == 'ready':
            try:
                subject = f'Your Order #{order.id} is Ready for Pickup - Royal Nepal'
                context = {
                    'order': order,
                    'restaurant_name': 'Royal Nepal Restaurant'
                }
                html_message = render_to_string('orders/emails/order_ready.html', context)
                plain_message = strip_tags(html_message)

                send_mail(
                    subject=subject,
                    message=plain_message,
                    html_message=html_message,
                    from_email='jithendrakatta9999@gmail.com',
                    recipient_list=[order.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending order ready email: {str(e)}")

        badge_class = {
            'pending': 'bg-warning',
            'in_progress': 'bg-info',
            'ready': 'bg-success',
            'completed': 'bg-secondary'
        }.get(new_status, 'bg-warning')

        return JsonResponse({
            'status': 'success',
            'new_status': order.get_status_display(),
            'badge_class': badge_class
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)


@user_passes_test(is_staff_or_superuser)
def order_stats(request):
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    if request.method == 'POST':
        start_date = datetime.strptime(request.POST.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.POST.get('end_date'), '%Y-%m-%d').date()

    orders_list = Order.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).order_by('-created_at')

    # Calculate stats
    stats = orders_list.aggregate(
        total_sales=Sum('total_amount'),
        order_count=Count('id')
    )

    total_sales = stats['total_sales'] or Decimal('0.00')
    order_count = stats['order_count']

    # Calculate average order value
    avg_order_value = Decimal('0.00')
    if order_count > 0:
        avg_order_value = total_sales / order_count

    # Calculate daily order counts for the chart
    date_range = (end_date - start_date).days + 1
    dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(date_range)]

    daily_orders = Order.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).values('created_at__date').annotate(
        count=Count('id')
    ).order_by('created_at__date')

    order_counts = {order['created_at__date'].strftime('%Y-%m-%d'): order['count'] for order in daily_orders}
    counts = [order_counts.get(date, 0) for date in dates]

    # Paginate orders
    paginator = Paginator(orders_list, 10)
    page = request.GET.get('page')

    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)

    context = {
        'orders': orders,
        'total_sales': total_sales,
        'order_count': order_count,
        'avg_order_value': round(avg_order_value, 2),
        'start_date': start_date,
        'end_date': end_date,
        'dates': json.dumps(dates),
        'counts': json.dumps(counts)
    }
    return render(request, 'restaurant_admin/order_stats.html', context)


###MANAGE RESERVATIONS


@user_passes_test(is_staff_or_superuser)
def reservations_by_date(request):
    selected_date = request.GET.get('date')
    if selected_date:
        try:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()

    reservations = Reservation.objects.filter(
        date=selected_date
    ).order_by('time')

    context = {
        'reservations': reservations,
        'selected_date': selected_date,
    }
    return render(request, 'restaurant_admin/reservations_by_date.html', context)


@user_passes_test(is_staff_or_superuser)
def get_reservations(request):
    selected_date = request.GET.get('date')
    try:
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        selected_date = timezone.now().date()

    # Get all reservations for the selected date
    reservations_list = Reservation.objects.filter(
        date=selected_date
    ).order_by('time')

    # Set up pagination
    paginator = Paginator(reservations_list, 10)
    page = request.GET.get('res_page')

    try:
        reservations = paginator.page(page)
    except PageNotAnInteger:
        reservations = paginator.page(1)
    except EmptyPage:
        reservations = paginator.page(paginator.num_pages)

    # Render both the table and pagination
    table_html = loader.render_to_string(
        'restaurant_admin/reservations_table.html',
        {'reservations': reservations, 'show_all': True},
        request=request
    )

    pagination_html = loader.render_to_string(
        'includes/pagination_style.html',
        {'items': reservations, 'page_param': 'res_page'},
        request=request
    )

    return JsonResponse({
        'html': table_html,
        'pagination': pagination_html
    })


@user_passes_test(is_staff_or_superuser)
def update_arrival_status(request, reservation_id):
    if request.method == 'POST':
        reservation = get_object_or_404(Reservation, id=reservation_id)
        arrival_status = request.POST.get('status')

        if arrival_status in ['not_arrived', 'seated', 'no_show']:
            reservation.arrival_status = arrival_status
            reservation.save()

            return JsonResponse({
                'status': 'success',
                'new_status': arrival_status,
                'message': 'Arrival status updated successfully'
            })

    return JsonResponse({'error': 'Invalid request'}, status=400)

@user_passes_test(is_staff_or_superuser)
def update_reservation_status(request, reservation_id):
    if request.method == 'POST':
        reservation = get_object_or_404(Reservation, id=reservation_id)
        action = request.POST.get('action')

        if action == 'approve':
            reservation.status = 'confirmed'
            send_reservation_email(
                reservation,
                'reservation_confirmation',
                'Reservation Confirmed - Royal Nepal Restaurant'
            )
        elif action == 'reject':
            reservation.status = 'rejected'
            send_reservation_email(
                reservation,
                'reservation_rejected',
                'Reservation Not Available - Royal Nepal Restaurant'
            )

        reservation.save()
        return JsonResponse({
            'status': 'success',
            'new_status': reservation.get_status_display()
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)

# Helper function for sending emails
def send_reservation_email(reservation, template_name, subject):
    if not reservation.is_manual_entry:  # Only send for online reservations
        try:
            context = {'reservation': reservation}
            html_message = render_to_string(f'reservations/emails/{template_name}.html', context)
            plain_message = strip_tags(html_message)
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email='jithendrakatta9999@gmail.com',
                recipient_list=[reservation.email],
                fail_silently=False,
            )
            print(f"Reservation email sent to {reservation.email}")
        except Exception as e:
            print(f"Error sending reservation email: {str(e)}")

@user_passes_test(is_staff_or_superuser)
def reservation_details(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    context = {
        'reservation': reservation
    }
    return render(request, 'restaurant_admin/reservation_details.html', context)




@user_passes_test(is_staff_or_superuser)
def add_manual_reservation(request):
    if request.method == 'POST':
        try:
            reservation = Reservation.objects.create(
                user=request.user,
                name=request.POST['name'],
                email=request.POST.get('email', ''),
                phone=request.POST['phone'],
                date=request.POST['date'],
                time=request.POST['time'],
                guests=request.POST['guests'],
                special_request=request.POST.get('special_request', ''),
                status='confirmed',
                is_manual_entry=True
            )
            messages.success(request, 'Reservation added successfully')
        except Exception as e:
            messages.error(request, f'Error adding reservation: {str(e)}')
    return redirect('restaurant_admin:dashboard')


###MANAGE PAYMENTS


@user_passes_test(is_staff_or_superuser)
def manage_payments(request):
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    user_id = request.GET.get('user_id')  # For filtering by specific user

    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

    # Base queryset
    transactions = Transaction.objects.select_related('user')

    # Apply filters
    if user_id:
        transactions = transactions.filter(user_id=user_id)

    transactions = transactions.filter(
        created_at__date__range=[start_date, end_date]
    ).order_by('-created_at')

    # Calculate summary stats
    stats = transactions.aggregate(
        total_amount=Sum('amount'),
        total_refunded=Sum('refunded_amount'),
        total_transactions=Count('id')  # Add this line
    )

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(transactions, 10)  # 10 items per page

    try:
        transactions = paginator.page(page)
    except PageNotAnInteger:
        transactions = paginator.page(1)
    except EmptyPage:
        transactions = paginator.page(paginator.num_pages)

    context = {
        'transactions': transactions,
        'start_date': start_date,
        'end_date': end_date,
        'total_amount': stats['total_amount'] or 0,
        'total_refunded': stats['total_refunded'] or 0,
        'total_transactions': stats['total_transactions'] or 0,  # Add this line
        'page_obj': transactions,
    }

    return render(request, 'restaurant_admin/manage_payments.html', context)


@user_passes_test(is_staff_or_superuser)
def get_transaction_details(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)

    return JsonResponse({
        'id': transaction.id,
        'date': transaction.created_at.strftime('%Y-%m-%d %H:%M'),
        'customer_name': transaction.user.get_full_name() if transaction.user else 'Guest',
        'amount': float(transaction.amount),
        'status': transaction.get_status_display(),
        'payment_method': transaction.payment_method,
        'can_refund': transaction.can_be_refunded(),
        'refunded_amount': float(transaction.refunded_amount)
    })


@user_passes_test(is_staff_or_superuser)
def process_refund(request, transaction_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    try:
        transaction = get_object_or_404(Transaction, id=transaction_id)

        if transaction.status == 'refunded':
            return JsonResponse({'error': 'Transaction has already been refunded'}, status=400)

        if not transaction.can_be_refunded():
            return JsonResponse({'error': 'This transaction cannot be refunded'}, status=400)

        data = json.loads(request.body)
        refund_amount = Decimal(str(data.get('amount', '0')))
        reason = data.get('reason', '')

        if refund_amount <= 0 or refund_amount > transaction.amount:
            return JsonResponse({'error': 'Invalid refund amount'}, status=400)

        # Process refund through payment gateway
        if transaction.payment_method == 'stripe':
            refund = stripe.Refund.create(
                payment_intent=transaction.payment_id,
                amount=int(refund_amount * 100)  # Convert to cents for Stripe
            )
            refund_id = refund.id
        else:
            # Handle other payment methods or manual refunds
            refund_id = f'MANUAL-{uuid.uuid4()}'

        # Update transaction status
        transaction.status = 'refunded'
        transaction.refunded_amount = refund_amount
        transaction.refund_reason = reason
        transaction.refunded_by = request.user
        transaction.refunded_at = timezone.now()
        transaction.save()

        # Create refund transaction record
        Transaction.objects.create(
            user=transaction.user,
            transaction_type='refund',
            amount=-refund_amount,  # Negative amount for refund
            status='completed',
            payment_method=transaction.payment_method,
            payment_id=refund_id,
            reference_id=transaction.reference_id,
            description=f'Refund for transaction #{transaction.id}: {reason}'
        )
        send_refund_confirmation_email(transaction, refund_amount, reason)

        return JsonResponse({
            'status': 'success',
            'message': 'Refund processed successfully'
        })

    except stripe.error.StripeError as e:
        return JsonResponse({
            'error': f'Payment gateway error: {str(e)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Error processing refund: {str(e)}'
        }, status=500)


def send_refund_confirmation_email(transaction, refund_amount, reason):
    """Send refund confirmation emails to customer and admin"""

    # Context for email templates
    context = {
        'transaction': transaction,
        'refund_amount': refund_amount,
        'reason': reason,
        'restaurant_name': 'Royal Nepal Restaurant'
    }

    # Customer Email
    try:
        customer_subject = f'Refund Processed - Royal Nepal Restaurant'
        customer_html = render_to_string('restaurant_admin/emails/refund_customer_email.html', context)
        customer_text = strip_tags(customer_html)

        send_mail(
            subject=customer_subject,
            message=customer_text,
            html_message=customer_html,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[transaction.user.email],
            fail_silently=False
        )

    except Exception as e:
        print(f"Error sending customer refund email: {str(e)}")

    # Admin Notification
    try:
        admin_subject = f'Refund Processed for Transaction #{transaction.id}'
        admin_html = render_to_string('restaurant_admin/emails/refund_admin_email.html', context)
        admin_text = strip_tags(admin_html)

        send_mail(
            subject=admin_subject,
            message=admin_text,
            html_message=admin_html,
            from_email= 'jithendrakatta9999@gmail.com', #settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.RESTAURANT_ORDER_EMAIL],
            fail_silently=False
        )

    except Exception as e:
        print(f"Error sending admin refund email: {str(e)}")


@user_passes_test(is_staff_or_superuser)
def customer_transactions(request, user_id):
    """View for showing transactions for a specific customer"""
    return manage_payments(request)





###MENU MANAGEMENT

@user_passes_test(is_staff_or_superuser)
@require_POST
def add_category(request):
    try:
        data = json.loads(request.body)
        category = Category.objects.create(
            name=data['name'],
            description=data.get('description', ''),
            display_order=data.get('display_order', 0)
        )
        return JsonResponse({
            'status': 'success',
            'category': {
                'id': category.id,
                'name': category.name,
                'item_count': 0
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@user_passes_test(is_staff_or_superuser)
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'GET':
        return JsonResponse({
            'name': category.name,
            'description': category.description,
            'display_order': category.display_order
        })

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            category.name = data['name']
            category.description = data.get('description', '')
            category.display_order = int(data.get('display_order', 0))
            category.save()

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@user_passes_test(is_staff_or_superuser)
@require_POST
def delete_category(request, category_id):
    try:
        category = get_object_or_404(Category, id=category_id)

        # Check if category has menu items
        if category.items.exists():
            # Option 1: Prevent deletion
            return JsonResponse({
                'status': 'error',
                'message': 'Cannot delete category that contains menu items'
            }, status=400)

            # Option 2: Delete all related items
            # category.items.all().delete()

        category.delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@user_passes_test(is_staff_or_superuser)
def get_menu_item(request, item_id):
    try:
        item = get_object_or_404(MenuItem, id=item_id)
        data = {
            'id': item.id,
            'name': item.name,
            'category_id': item.category.id,
            'price': str(item.price),
            'description': item.description,
            'spice_level': item.spice_level,
            'is_available': item.is_available,
        }
        if item.image:
            data['image_url'] = item.image.url
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@user_passes_test(is_staff_or_superuser)
def add_menu_item(request):
    if request.method == 'POST':
        try:
            menu_item = MenuItem.objects.create(
                name=request.POST['name'],
                category_id=request.POST['category'],
                price=request.POST['price'],
                description=request.POST.get('description', ''),
                spice_level=request.POST.get('spice_level', 'medium'),
                is_available=request.POST.get('is_available') == 'on'
            )

            if 'image' in request.FILES:
                menu_item.image = request.FILES['image']
                menu_item.save()

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@user_passes_test(is_staff_or_superuser)
def edit_menu_item(request, item_id):
    menu_item = get_object_or_404(MenuItem, id=item_id)

    if request.method == 'POST':
        try:
            menu_item.name = request.POST['name']
            menu_item.category_id = request.POST['category']
            menu_item.price = request.POST['price']
            menu_item.description = request.POST.get('description', '')
            menu_item.spice_level = request.POST.get('spice_level', 'medium')
            menu_item.is_available = request.POST.get('is_available') == 'on'

            if 'image' in request.FILES:
                # Delete old image if exists
                if menu_item.image:
                    menu_item.image.delete()
                menu_item.image = request.FILES['image']

            menu_item.save()
            return JsonResponse({'status': 'success'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@user_passes_test(is_staff_or_superuser)
@require_POST
def delete_menu_item(request, item_id):
    try:
        menu_item = get_object_or_404(MenuItem, id=item_id)
        if menu_item.image:
            default_storage.delete(menu_item.image.path)
        menu_item.delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@user_passes_test(is_staff_or_superuser)
@require_POST
def toggle_menu_item(request, item_id):
    try:
        menu_item = get_object_or_404(MenuItem, id=item_id)
        menu_item.is_available = not menu_item.is_available
        menu_item.save()
        return JsonResponse({
            'status': 'success',
            'is_available': menu_item.is_available
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@user_passes_test(is_staff_or_superuser)
def food_menu(request):
    categories = Category.objects.all().order_by('display_order')
    menu_items = MenuItem.objects.select_related('category').all()

    context = {
        'categories': categories,
        'menu_items': menu_items,
    }
    return render(request, 'restaurant_admin/food_menu.html', context)




###MANAGE CUSTOMERS

@user_passes_test(is_staff_or_superuser)
def customer_management(request):
    # Get search parameter
    search_query = request.GET.get('search', '')

    # Get all customers with related user data and order stats
    customers_list = UserProfile.objects.select_related('user')

    # Apply search filter if provided
    if search_query:
        customers_list = customers_list.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )

    # Add annotations for order stats
    customers_list = customers_list.annotate(
        total_orders=Count('user__orders'),
        total_spent=Sum('user__orders__total_amount')
    ).order_by('-total_spent')

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(customers_list, 10)

    try:
        customers = paginator.page(page)
    except PageNotAnInteger:
        customers = paginator.page(1)
    except EmptyPage:
        customers = paginator.page(paginator.num_pages)

    context = {
        'customers': customers,
        'page_obj': customers,
        'search_query': search_query,
    }

    return render(request, 'restaurant_admin/customer_management.html', context)

# restaurant_admin/views.py

@user_passes_test(is_staff_or_superuser)
def customer_detail(request, user_id):
    customer = get_object_or_404(UserProfile, user_id=user_id)

    # Get transaction data
    transactions = Transaction.objects.filter(user_id=user_id)

    from django.db import models

    stats = transactions.aggregate(
        total_spent=Sum(Case(
            When(transaction_type='order', then='amount'),
            default=0,
            output_field=models.DecimalField(max_digits=10, decimal_places=2)  # Use models.DecimalField
        )),
        total_refunds=Sum(Case(
            When(transaction_type='refund', then='amount'),
            default=0,
            output_field=models.DecimalField(max_digits=10, decimal_places=2)  # Use models.DecimalField
        ))
    )

    # Get recent transactions
    recent_transactions = transactions.order_by('-created_at')[:5]
    last_transaction = transactions.order_by('-created_at').first()

    # Get order history with pagination
    orders_list = Order.objects.filter(user_id=user_id).prefetch_related('items__menu_item').order_by('-created_at')
    order_paginator = Paginator(orders_list, 10)
    order_page = request.GET.get('order_page')

    try:
        orders = order_paginator.page(order_page)
    except PageNotAnInteger:
        orders = order_paginator.page(1)
    except EmptyPage:
        orders = order_paginator.page(order_paginator.num_pages)

    # Get reservation history with pagination
    reservations_list = Reservation.objects.filter(user_id=user_id).order_by('-date', '-time')
    res_paginator = Paginator(reservations_list, 10)
    res_page = request.GET.get('res_page')

    try:
        reservations = res_paginator.page(res_page)
    except PageNotAnInteger:
        reservations = res_paginator.page(1)
    except EmptyPage:
        reservations = res_paginator.page(res_paginator.num_pages)

    # Add page parameters for cross-referencing
    order_page_param = f'order_page={orders.number}' if orders else ''
    res_page_param = f'res_page={reservations.number}' if reservations else ''

    context = {
        'customer': customer,
        'total_orders': transactions.filter(transaction_type='order').count(),
        'total_spent': stats['total_spent'] or Decimal('0.00'),
        'total_refunds': abs(stats['total_refunds'] or Decimal('0.00')),
        'last_transaction_date': last_transaction.created_at if last_transaction else None,
        'recent_transactions': recent_transactions,
        'orders': orders,
        'reservations': reservations,
        'order_page_param': order_page_param,
        'res_page_param': res_page_param
        # ... rest of your existing context ...
    }
    return render(request, 'restaurant_admin/customer_detail.html', context)



###MANAGE GIFTCARDS


@user_passes_test(is_staff_or_superuser)
def manage_giftcards(request):
    # Get search parameter
    search_query = request.GET.get('search', '')

    # Base queryset
    giftcards_list = GiftCard.objects.all()

    # Apply search filter if provided
    if search_query:
        giftcards_list = giftcards_list.filter(
            Q(card_number__icontains=search_query) |
            Q(recipient_name__icontains=search_query) |
            Q(recipient_email__icontains=search_query)
        )

    # Order by purchase date
    giftcards_list = giftcards_list.order_by('-purchase_date')

    # Calculate summary stats
    stats = {
        'total_cards': giftcards_list.count(),
        'total_value': giftcards_list.aggregate(Sum('amount'))['amount__sum'] or 0,
        'active_cards': giftcards_list.filter(status='active').count()
    }

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(giftcards_list, 10)

    try:
        giftcards = paginator.page(page)
    except PageNotAnInteger:
        giftcards = paginator.page(1)
    except EmptyPage:
        giftcards = paginator.page(paginator.num_pages)

    context = {
        'gift_cards': giftcards,
        'stats': stats,
        'page_obj': giftcards,
        'search_query': search_query,
        'page_title': 'Gift Card Management',
        'section': 'giftcards',
    }

    return render(request, 'restaurant_admin/giftcard_management.html', context)


@user_passes_test(is_staff_or_superuser)
def validate_giftcard(request):
    if request.method != 'POST':
        return JsonResponse({'valid': False, 'message': 'Invalid request method'})

    try:
        data = json.loads(request.body)
        card_number = data.get('card_number')
        code = data.get('code')

        card = get_object_or_404(GiftCard, card_number=card_number)

        # Verify the code matches the card's UUID
        # You might want to implement a more secure verification method
        if str(card.card_id) == code:
            return JsonResponse({
                'valid': True,
                'balance': float(card.balance)
            })
        return JsonResponse({
            'valid': False,
            'message': 'Invalid verification code'
        })
    except Exception as e:
        return JsonResponse({
            'valid': False,
            'message': str(e)
        })


@user_passes_test(is_staff_or_superuser)
def redeem_giftcard(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})

    try:
        data = json.loads(request.body)
        card_number = data.get('card_number')
        amount = Decimal(str(data.get('amount', 0)))

        card = get_object_or_404(GiftCard, card_number=card_number)

        if not card.is_valid():
            return JsonResponse({
                'success': False,
                'message': 'Gift card is invalid or expired'
            })

        if amount > card.balance:
            return JsonResponse({
                'success': False,
                'message': 'Insufficient balance'
            })

        # Process redemption
        card.balance -= amount
        if card.balance == 0:
            card.status = 'redeemed'
        card.save()

        # Create transaction record
        GiftCardTransaction.objects.create(
            gift_card=card,
            transaction_type='redemption',
            amount=amount,
            user=request.user
        )

        return JsonResponse({
            'success': True,
            'new_balance': float(card.balance)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

### Settings


# restaurant_admin/views.py

@user_passes_test(is_staff_or_superuser)
def settings(request):
    announcements = Announcement.objects.all().order_by('-created_at')
    return render(request, 'restaurant_admin/settings.html', {
        'announcements': announcements
    })


@user_passes_test(is_staff_or_superuser)
def update_account(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

    try:
        user = request.user

        # Update basic info
        user.first_name = request.POST.get('name', '').split()[0]
        user.last_name = ' '.join(request.POST.get('name', '').split()[1:])
        user.email = request.POST.get('email')

        # Handle password change if provided
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if current_password and new_password:
            if not user.check_password(current_password):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Current password is incorrect'
                })

            if new_password != confirm_password:
                return JsonResponse({
                    'status': 'error',
                    'message': 'New passwords do not match'
                })

            user.set_password(new_password)

        user.save()
        return JsonResponse({'status': 'success'})

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })



@user_passes_test(is_staff_or_superuser)
def add_announcement(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

    try:
        # Parse the datetime strings and make them timezone-aware
        start_date = parse_datetime(request.POST['start_date'])
        end_date = parse_datetime(request.POST['end_date'])

        # If dates are naive, make them timezone-aware using the current timezone
        if timezone.is_naive(start_date):
            start_date = timezone.make_aware(start_date)
        if timezone.is_naive(end_date):
            end_date = timezone.make_aware(end_date)

        announcement = Announcement.objects.create(
            title=request.POST['title'],
            message=request.POST['message'],
            start_date=start_date,
            end_date=end_date,
            frequency=request.POST['frequency'],
            is_active=bool(request.POST.get('is_active'))
        )

        if 'image' in request.FILES:
            announcement.image = request.FILES['image']
            announcement.save()

        return JsonResponse({'status': 'success'})

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })


@user_passes_test(is_staff_or_superuser)
def edit_announcement(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id)

    if request.method == 'GET':
        # Convert timezone-aware dates to ISO format for the frontend
        return JsonResponse({
            'id': announcement.id,
            'title': announcement.title,
            'message': announcement.message,
            'start_date': announcement.start_date.astimezone(timezone.get_current_timezone()).strftime(
                '%Y-%m-%dT%H:%M'),
            'end_date': announcement.end_date.astimezone(timezone.get_current_timezone()).strftime('%Y-%m-%dT%H:%M'),
            'frequency': announcement.frequency,
            'is_active': announcement.is_active,
            'image_url': announcement.image.url if announcement.image else None
        })

    elif request.method == 'POST':
        try:
            # Parse and make dates timezone-aware
            start_date = parse_datetime(request.POST['start_date'])
            end_date = parse_datetime(request.POST['end_date'])

            if timezone.is_naive(start_date):
                start_date = timezone.make_aware(start_date)
            if timezone.is_naive(end_date):
                end_date = timezone.make_aware(end_date)

            announcement.title = request.POST['title']
            announcement.message = request.POST['message']
            announcement.start_date = start_date
            announcement.end_date = end_date
            announcement.frequency = request.POST['frequency']
            announcement.is_active = bool(request.POST.get('is_active'))

            if 'image' in request.FILES:
                if announcement.image:
                    announcement.image.delete()
                announcement.image = request.FILES['image']

            announcement.save()
            return JsonResponse({'status': 'success'})

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@user_passes_test(is_staff_or_superuser)
def delete_announcement(request, announcement_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

    try:
        announcement = get_object_or_404(Announcement, id=announcement_id)
        if announcement.image:
            announcement.image.delete()
        announcement.delete()
        return JsonResponse({'status': 'success'})

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })