# orders/views.py
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import stripe
from django.urls import reverse

from accounts.models import Transaction
from restaurant_admin.models import StoreStatus
from .models import Order, OrderItem
from menu.models import MenuItem, ItemAddon, ItemChoice
import json
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from decimal import Decimal
from django.utils.html import strip_tags
from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import now
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger




# Add these functions to orders/views.py
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from .payment import create_payment_intent, confirm_payment
from .payment_methods import ApplePayClient, PayPalClient


def send_order_confirmation_email(order):
    """Send order confirmation email to customer"""
    # Calculate tax and total
    tax_rate = Decimal('0.13')
    tax_amount = order.total_amount * tax_rate
    total_with_tax = order.total_amount + tax_amount

    context = {
        'order': order,
        'tax_amount': tax_amount,
        'total_with_tax': total_with_tax,
        'logo_url': 'https://yoursite.com/static/img/logo.png',  # Update with your logo URL
        'admin_url': f'https://yoursite.com/restaurant-admin/order/{order.id}/',  # Update with your admin URL
    }

    # Customer email
    customer_subject = f'Order Confirmation - Order #{order.id}'
    customer_html_message = render_to_string('orders/emails/customer_order_email.html', context)
    customer_plain_message = strip_tags(customer_html_message)

    send_mail(
        subject=customer_subject,
        message=customer_plain_message,
        html_message=customer_html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.email],
        fail_silently=False,
    )

    # Restaurant notification email
    admin_subject = f'New Order #{order.id} Received'
    admin_html_message = render_to_string('orders/emails/restaurant_order_email.html', context)
    admin_plain_message = strip_tags(admin_html_message)

    send_mail(
        subject=admin_subject,
        message=admin_plain_message,
        html_message=admin_html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.RESTAURANT_ORDER_EMAIL],
        fail_silently=False,
    )


def cart_detail(request):
    cart = request.session.get('cart', {})
    cart_items = []
    cart_total = Decimal('0.00')
    invalid_items = []

    for item_key, item_data in cart.items():
        try:
            # Split the composite key carefully
            parts = item_key.split('_')

            # Ensure we have at least the item ID
            if len(parts) >= 1:
                item_id = parts[0]
                try:
                    menu_item = MenuItem.objects.get(id=item_id)

                    # Get the stored price from cart data
                    item_price = Decimal(str(item_data.get('price', menu_item.price)))
                    quantity = item_data.get('quantity', 1)
                    item_total = item_price * quantity
                    cart_total += item_total

                    # Prepare customization details
                    choice_name = None
                    choice = None
                    if item_data.get('choice_id'):
                        try:
                            choice = ItemChoice.objects.get(id=item_data['choice_id'])
                            choice_name = choice.name
                        except ItemChoice.DoesNotExist:
                            pass

                    # Prepare addon details
                    addon_names = []
                    addons = []
                    if item_data.get('addon_ids'):
                        addon_ids = item_data['addon_ids']
                        for addon_id in addon_ids:
                            try:
                                addon = ItemAddon.objects.get(id=addon_id)
                                addons.append(addon)
                                addon_names.append(addon.name)
                            except ItemAddon.DoesNotExist:
                                pass

                    cart_items.append({
                        'menu_item': menu_item,
                        'quantity': quantity,
                        'price': item_price,
                        'total_price': item_total,
                        'choice_name': choice_name,
                        'choice': choice,
                        'addon_names': addon_names,
                        'addons': addons,
                        'special_instructions': item_data.get('special_instructions', ''),
                        'key': item_key  # Store the original key
                    })
                except MenuItem.DoesNotExist:
                    invalid_items.append(item_key)
                    continue

        except Exception as e:
            print(f"Error processing cart item {item_key}: {str(e)}")
            invalid_items.append(item_key)
            continue

    # Remove invalid items from cart
    if invalid_items:
        for item_key in invalid_items:
            cart.pop(item_key, None)
        request.session['cart'] = cart
        request.session.modified = True

    tax_rate = Decimal('0.13')
    tax_amount = round(cart_total * tax_rate, 2)
    total_with_tax = cart_total + tax_amount

    return render(request, 'orders/cart_detail.html', {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'tax_amount': tax_amount,
        'total_with_tax': total_with_tax
    })
def check_store_status(request):
    try:
        #print("\n=== Checking Store Status -orders===")

        current_time = timezone.localtime()
        current_hour = current_time.hour
        # print(f"Current time: {current_time}")
        # print(f"Current hour: {current_hour}")

        # Check store hours (12 PM to 9 PM)
        # if current_hour < 12 or current_hour >= 21:
        #     return JsonResponse({
        #         'status': 'closed',
        #         'message': 'Store is closed. Our hours are 12:00 PM to 9:00 PM.'
        #     })

        # Get store status from admin settings
        status_obj = StoreStatus.objects.first()  # Changed from get_current_status()
        # print(f"Retrieved status object: {status_obj}")

        if not status_obj:
            # Create default status if none exists
            # print("No status found, creating default open status")
            status_obj = StoreStatus.objects.create(status='open')

        # print(f"Current store status: {status_obj.status}")
        # print("=== Store Status Check Complete -orders===\n")

        if status_obj.status == 'closed':
            message = 'Store is currently closed.'
        elif status_obj.status == 'paused':
            message = 'Orders are temporarily paused. Please try again later.'
        else:
            message = 'Store is open.'

        return JsonResponse({
            'status': status_obj.status,
            'message': message
        })
    except Exception as e:
        print(f"Error checking store status: {str(e)}")  # For debugging
        # Default to open if there's an error
        return JsonResponse({
            'status': 'open',
            'message': 'Store is open'
        })

@csrf_protect
@require_http_methods(["POST"])
def save_cart(request):
    cart_data = json.loads(request.body)
    request.session['cart'] = cart_data
    return JsonResponse({'status': 'success'})


def get_cart(request):
    cart = request.session.get('cart', {})
    return JsonResponse(cart)


# In orders/views.py

@login_required
def checkout(request):
    store_status = StoreStatus.get_current_status()
    current_time = timezone.localtime()

    # Store status checks
    if store_status == 'closed':
        messages.error(request, 'Store is currently closed.')
        return redirect('orders:cart_detail')
    elif store_status == 'paused':
        messages.warning(request, 'Orders are temporarily paused. Please try again after 30 minutes.')
        return redirect('orders:cart_detail')

    # Get cart data
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, 'Your cart is empty!')
        return redirect('menu:menu_list')

    try:
        # Calculate cart totals with precise processing
        cart_items = []
        cart_total = Decimal('0.00')

        for item_key, item_data in cart.items():
            # Carefully extract item ID
            try:
                parts = item_key.split('_')
                item_id = parts[0]

                menu_item = MenuItem.objects.get(id=item_id)

                # Get the stored price from cart data
                item_price = Decimal(str(item_data.get('price', menu_item.price)))
                quantity = item_data.get('quantity', 1)
                item_total = item_price * quantity
                cart_total += item_total

                # Prepare choice details
                choice = None
                choice_name = None
                if item_data.get('choice_id'):
                    try:
                        choice = ItemChoice.objects.get(id=item_data['choice_id'])
                        choice_name = choice.name
                        #item_total += Decimal(str(choice.price_adjustment)) * quantity
                    except ItemChoice.DoesNotExist:
                        pass

                # Prepare addon details
                addons = []
                addon_names = []
                if item_data.get('addon_ids'):
                    for addon_id in item_data['addon_ids']:
                        try:
                            addon = ItemAddon.objects.get(id=addon_id)
                            addons.append(addon)
                            addon_names.append(addon.name)
                            #item_total += Decimal(str(addon.price)) * quantity
                        except ItemAddon.DoesNotExist:
                            pass

                cart_items.append({
                    'menu_item': menu_item,
                    'quantity': quantity,
                    'price': item_price,
                    'total_price': item_total,
                    'choice': choice,
                    'choice_name': choice_name,
                    'addons': addons,
                    'addon_names': addon_names,
                    'special_instructions': item_data.get('special_instructions', '')
                })
            except MenuItem.DoesNotExist:
                continue

        tax_rate = Decimal('0.13')
        tax_amount = round(cart_total * tax_rate, 2)
        total_with_tax = cart_total + tax_amount

        if request.method == 'POST':
            # Handle JSON requests (online payments)
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                tip_amount = Decimal(str(data.get('tip_amount', '0')))

                # Handle rewards for online payment
                rewards_used = Decimal('0')
                if data.get('use_rewards'):
                    rewards_amount = Decimal(str(data.get('rewards_amount', '0')))
                    if rewards_amount > request.user.profile.rewards_balance:
                        return JsonResponse({
                            'error': 'Insufficient rewards balance'
                        }, status=400)
                    rewards_used = rewards_amount

                final_total = total_with_tax + tip_amount - rewards_used

                # Create payment intent with updated metadata
                intent = stripe.PaymentIntent.create(
                    amount=int(final_total * 100),
                    currency='usd',
                    automatic_payment_methods={'enabled': True},
                    metadata={
                        'customer_email': data.get('email'),
                        'cart_items': json.dumps([{
                            'item_id': str(item['menu_item'].id),
                            'quantity': item['quantity'],
                            'choice_id': item['choice'].id if item['choice'] else None,
                            'addon_ids': [addon.id for addon in item['addons']] if item['addons'] else [],
                            'special_instructions': item['special_instructions']
                        } for item in cart_items]),
                        'tip_amount': str(tip_amount),
                        'rewards_used': str(rewards_used),
                        'user_id': str(request.user.id),
                        'customer_name': data.get('name'),
                        'phone': data.get('phone'),
                        'special_instructions': data.get('special_instructions', '')
                    }
                )

                return JsonResponse({
                    'client_secret': intent.client_secret,
                    'amount': float(final_total)
                })

            # Handle regular form submission (pay at pickup)
            else:
                # Get rewards amount if being used
                rewards_used = Decimal('0')
                if request.POST.get('use_rewards'):
                    rewards_amount = Decimal(request.POST.get('rewards_amount', '0'))
                    if rewards_amount > request.user.profile.rewards_balance:
                        messages.error(request, 'Insufficient rewards balance')
                        return redirect('orders:checkout')
                    rewards_used = rewards_amount

                tip_amount = Decimal(request.POST.get('tip_amount', '0'))
                final_total = total_with_tax + tip_amount - rewards_used

                # Create order
                order = Order.objects.create(
                    user=request.user,
                    name=request.POST.get('name'),
                    email=request.POST.get('email'),
                    phone=request.POST.get('phone'),
                    payment_method='in_store',
                    special_instructions=request.POST.get('special_instructions', ''),
                    tip_amount=tip_amount,
                    total_amount=final_total,
                    rewards_used=rewards_used,
                    status='pending',
                    payment_status='pending'
                )

                # Create order items with full customization details
                for item in cart_items:
                    order_item = OrderItem.objects.create(
                        order=order,
                        menu_item=item['menu_item'],
                        quantity=item['quantity'],
                        price=item['price']
                    )

                    # Add choice if exists
                    if item['choice']:
                        order_item.choice = item['choice']
                        order_item.save()

                    # Add addons if exists
                    if item['addons']:
                        order_item.addons.add(*item['addons'])

                profile = request.user.profile
                profile.rewards_balance -= rewards_used
                profile.save()

                # Calculate and save points earned (based on amount paid without rewards)
                points_earned = int(((final_total + rewards_used) / Decimal('100.00')) * 1000)
                order.points_earned = points_earned

                order.save()

                # Clear cart
                request.session['cart'] = {}

                # Send admin notification
                try:
                    notify_admin("new_order", {
                        "id": order.id,
                        "time": order.created_at.strftime("%H:%M"),
                        "total": str(order.total_amount),
                        "status": order.get_status_display(),
                        "customer_name": order.name,
                        "items_count": order.items.count(),
                        "payment_method": order.get_payment_method_display()
                    })
                except Exception as e:
                    print(f"Error sending notification to admin: {e}")

                # Send confirmation email
                try:
                    send_order_confirmation_email(order)
                except Exception as e:
                    print(f"Error sending confirmation email: {e}")

                messages.success(request, 'Order placed successfully! Please pay at pickup.')
                return redirect('orders:order_success', order_id=order.id)

        # GET request - render checkout page
        context = {
            'cart_items': cart_items,
            'cart_total': cart_total,
            'tax_amount': tax_amount,
            'total_with_tax': total_with_tax,
            'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
            'user': request.user
        }
        return render(request, 'orders/checkout.html', context)

    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        print("Error occurred: ", str(e))
        return redirect('orders:cart_detail')

@login_required
def my_orders(request):
    # Get all orders first
    order_list = Order.objects.filter(user=request.user).order_by('-created_at')

    # Calculate totals with proper decimal formatting
    total_spent = Decimal(str(order_list.aggregate(total=Sum('total_amount'))['total'] or '0')).quantize(
        Decimal('0.01'))

    # Calculate points correctly ($1 = 10 points)
    total_points_earned = 0
    for order in order_list:
        if order.status == 'completed':
            # Calculate points based on amount paid after rewards
            actual_paid = order.total_amount - (order.rewards_used or Decimal('0.00'))
            points = int(actual_paid * 10)  # $1 = 10 points
            total_points_earned += points

    # Add is_recent flag to all orders
    current_time = now()
    for order in order_list:
        order.is_recent = current_time - order.created_at < timedelta(minutes=5)

    # Set up pagination
    paginator = Paginator(order_list, 10)  # Show 10 orders per page
    page = request.GET.get('page')

    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        orders = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        orders = paginator.page(paginator.num_pages)

    # Make sure is_recent flag persists through pagination
    for order in orders:
        if not hasattr(order, 'is_recent'):
            order.is_recent = current_time - order.created_at < timedelta(minutes=5)

    return render(request, 'orders/my_orders.html', {
        'orders': orders,
        'total_spent': total_spent,
        'total_points_earned': total_points_earned,
    })


# In orders/views.py
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Calculate tax and total with tip
    tax_rate = Decimal('0.13')
    tax_amount = order.total_amount * tax_rate
    total_with_tip = order.total_amount + order.tip_amount

    return render(request, 'orders/order_success.html', {
        'order': order,
        'tax_amount': tax_amount,
        'total_with_tip': total_with_tip
    })


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Calculate tax and total with tip
    tax_rate = Decimal('0.13')
    tax_amount = order.total_amount * tax_rate
    total_with_tip = order.total_amount + order.tip_amount

    return render(request, 'orders/order_detail.html', {
        'order': order,
        'tax_amount': tax_amount,
        'total_with_tip': total_with_tip
    })

@login_required
def repeat_order(request, order_id):
    original_order = get_object_or_404(Order, id=order_id, user=request.user)

    # Create a new cart based on the original order
    cart = {}
    for order_item in original_order.items.all():
        cart[order_item.menu_item.id] = {
            'name': order_item.menu_item.name,
            'price': float(order_item.menu_item.price),
            'quantity': order_item.quantity
        }

    # Save the cart to the session
    request.session['cart'] = cart

    return redirect('orders:cart_detail')

@login_required
def process_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.payment_status == 'paid':
        messages.warning(request, 'This order has already been paid for.')
        return redirect('orders:order_success', order_id=order.id)

    # Create payment intent
    intent = create_payment_intent(order)
    if not intent:
        messages.error(request, 'Error creating payment. Please try again.')
        return redirect('orders:checkout')

    context = {
        'order': order,
        'client_secret': intent.client_secret,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, 'orders/payment.html', context)


@login_required
def create_payment_intent(request):
    print("Entered the create_payment_intent view")
    if request.method != 'POST':
        print("Received non-POST request, returning error")
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    try:
        print("Parsing request body")
        data = json.loads(request.body)
        print("Parsed request body: ", data.get('order_id'))
        order_id = data.get('order_id')

        order = get_object_or_404(Order, id=order_id, user=request.user)
        print(f"Found order: {order.id}")

        # Create payment intent
        try:
            print("Creating payment intent")

            intent = stripe.PaymentIntent.create(
                amount=int(order.total_amount * 100),  # Convert to cents
                currency='usd',
                automatic_payment_methods={
                    'enabled': True
                },
                metadata={
                    'order_id': order.id,
                    'customer_email': order.email
                }
            )
            print(f"Created payment intent: {intent.client_secret}")

        except stripe.error.StripeError as e:
            # Handle Stripe-specific errors
            return JsonResponse({'error': str(e.user_message)}, status=400)
        except Exception as e:
            # Handle other exceptions
            return JsonResponse({'error': 'An unexpected error occurred. Please try again.'}, status=400)

        return JsonResponse({
            'client_secret': intent.client_secret,
            'amount': float(order.total_amount)
        })
    except Exception as e:
        # Handle any other unexpected exceptions
        return JsonResponse({'error': 'An unexpected error occurred. Please try again.'}, status=400)


@login_required
def payment_success(request):
    payment_intent_id = request.GET.get('payment_intent')
    try:
        # Verify the payment with Stripe
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        if payment_intent.status == 'succeeded':
            # Get metadata from payment intent
            metadata = payment_intent.metadata
            cart_items = json.loads(metadata.get('cart_items', '[]'))

            # Create order after successful payment
            order = Order.objects.create(
                user=request.user,
                name=metadata.get('customer_name'),
                email=metadata.get('customer_email'),
                phone=metadata.get('phone'),
                payment_method='card',
                special_instructions=metadata.get('special_instructions', ''),
                tip_amount=Decimal(metadata.get('tip_amount', '0')),
                total_amount=Decimal(payment_intent.amount) / 100,
                rewards_used=Decimal(metadata.get('rewards_used', '0')),
                status='pending',
                payment_status='paid'
            )

            # Create order items with choices and addons
            for item_data in cart_items:
                menu_item = get_object_or_404(MenuItem, id=item_data['item_id'])
                order_item = OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=item_data['quantity'],
                    price=menu_item.price,
                    special_instructions=item_data.get('special_instructions', '')
                )

                # Add choice if selected
                if item_data.get('choice_id'):
                    try:
                        choice = menu_item.available_choices.get(id=item_data['choice_id'])
                        order_item.choice = choice
                        order_item.save()
                    except ItemChoice.DoesNotExist:
                        pass

                # Add addons if selected
                if item_data.get('addon_ids'):
                    for addon_id in item_data['addon_ids']:
                        try:
                            addon = menu_item.available_addons.get(id=addon_id)
                            order_item.addons.add(addon)
                        except ItemAddon.DoesNotExist:
                            pass

            # Create transaction record
            Transaction.objects.create(
                user=request.user,
                transaction_type='order',
                amount=order.total_amount,
                status='completed',
                payment_method='stripe',
                payment_id=payment_intent_id,
                reference_id=str(order.id),
                description=f'Order #{order.id}'
            )

            # Apply rewards if used
            rewards_used = Decimal(metadata.get('rewards_used', '0'))
            if rewards_used > 0:
                request.user.profile.use_rewards(rewards_used)

            # Clear cart
            request.session['cart'] = {}

            # Send admin notification
            try:
                notify_admin("new_order", {
                    "id": order.id,
                    "time": order.created_at.strftime("%H:%M"),
                    "total": str(order.total_amount),
                    "status": order.get_status_display(),
                    "customer_name": order.name,
                    "items_count": order.items.count(),
                    "payment_method": order.get_payment_method_display()
                })
            except Exception as e:
                print(f"Error sending notification to admin: {e}")

            # Send confirmation email
            try:
                send_order_confirmation_email(order)
            except Exception as e:
                print(f"Error sending confirmation email: {e}")

            messages.success(request, 'Payment successful! Your order has been confirmed.')
            return redirect('orders:order_success', order_id=order.id)

    except stripe.error.StripeError as e:
        messages.error(request, f'Payment verification failed: {str(e)}')
        return redirect('orders:cart_detail')
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('orders:cart_detail')

@login_required
def payment_cancel(request, order_id):
    messages.warning(request, 'Payment was cancelled. Please try again.')
    return redirect('orders:checkout')

#paypal_payments

@login_required
def create_paypal_order(request):
    data = json.loads(request.body)
    order = get_object_or_404(Order, id=data['order_id'], user=request.user)

    paypal_client = PayPalClient()
    response = paypal_client.create_order(order)

    return JsonResponse(response)


@login_required
def capture_paypal_payment(request):
    data = json.loads(request.body)
    paypal_client = PayPalClient()
    response = paypal_client.capture_payment(data['order_id'])

    if response.get('status') == 'COMPLETED':
        order_id = response['purchase_units'][0]['reference_id']
        order = Order.objects.get(id=order_id)
        order.payment_status = 'paid'
        order.save()

        send_order_confirmation_email(order)

    return JsonResponse(response)

@login_required
def paypal_success(request):
    """Handle successful PayPal payment return"""
    order_id = request.GET.get('order_id')
    if order_id:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        messages.success(request, 'PayPal payment successful! Your order has been confirmed.')
        return redirect('orders:order_success', order_id=order.id)
    messages.error(request, 'Error processing PayPal payment. Please contact support.')
    return redirect('orders:checkout')

@login_required
def paypal_cancel(request):
    """Handle cancelled PayPal payment"""
    order_id = request.GET.get('order_id')
    messages.warning(request, 'PayPal payment was cancelled. Please try again or choose a different payment method.')
    if order_id:
        return redirect('orders:checkout')
    return redirect('menu:menu_list')


#applepay_payments

@login_required
def validate_apple_pay(request):
    data = json.loads(request.body)
    apple_pay_client = ApplePayClient()
    merchant_session = apple_pay_client.validate_merchant_session(data['validationURL'])
    return JsonResponse(merchant_session)


@login_required
def process_apple_pay(request):
    data = json.loads(request.body)
    order = get_object_or_404(Order, id=data['order_id'], user=request.user)

    apple_pay_client = ApplePayClient()
    result = apple_pay_client.process_payment(data['payment'], order)

    if result['status'] == 'success':
        order.payment_status = 'paid'
        order.save()
        send_order_confirmation_email(order)

    return JsonResponse(result)

# Add these handler views to your views.py

@login_required
def apple_pay_success(request):
    """Handle successful Apple Pay payment return"""
    order_id = request.GET.get('order_id')
    if order_id:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        messages.success(request, 'Apple Pay payment successful! Your order has been confirmed.')
        return redirect('orders:order_success', order_id=order.id)
    messages.error(request, 'Error processing Apple Pay payment. Please contact support.')
    return redirect('orders:checkout')

@login_required
def apple_pay_cancel(request):
    """Handle cancelled Apple Pay payment"""
    order_id = request.GET.get('order_id')
    messages.warning(request, 'Apple Pay payment was cancelled. Please try again or choose a different payment method.')
    if order_id:
        return redirect('orders:checkout')
    return redirect('menu:menu_list')

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def notify_admin(notification_type, data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "admin_notifications",
        {
            "type": "notification_message",
            "message": {
                "type": notification_type,
                "data": data
            }
        }
    )