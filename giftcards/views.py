from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from accounts.models import Transaction
from .models import GiftCard, GiftCardTransaction
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from decimal import Decimal
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


# giftcards/views.py

@login_required
def purchase_giftcard(request):
    pending_giftcard = request.session.pop('pending_giftcard', None)

    if request.method == 'POST':
        try:
            # Get form data
            amount = request.POST.get('amount')
            recipient_name = request.POST.get('recipient_name')
            recipient_email = request.POST.get('recipient_email')
            message = request.POST.get('message', '')

            # Validate required fields
            if not all([amount, recipient_name, recipient_email]):
                return JsonResponse({
                    'error': 'All fields are required.'
                }, status=400)

            # Create gift card in pending state
            gift_card = GiftCard.objects.create(
                purchaser=request.user,
                amount=Decimal(amount),
                recipient_name=recipient_name,
                recipient_email=recipient_email,
                message=message,
                status='pending'
            )

            # Create payment intent
            # Option 1: Using automatic payment methods
            intent = stripe.PaymentIntent.create(
                amount=int(float(amount) * 100),  # Convert to cents
                currency='usd',
                automatic_payment_methods={
                    'enabled': True
                },
                metadata={
                    'gift_card_id': str(gift_card.card_id),
                    'customer_email': request.user.email
                }
            )

            # Option 2: If you prefer to specify payment methods explicitly, use this instead:
            # intent = stripe.PaymentIntent.create(
            #     amount=int(float(amount) * 100),
            #     currency='usd',
            #     payment_method_types=['card'],
            #     metadata={
            #         'gift_card_id': str(gift_card.card_id),
            #         'customer_email': request.user.email
            #     }
            # )

            return JsonResponse({
                'client_secret': intent.client_secret,
                'gift_card_id': str(gift_card.card_id)
            })

        except stripe.error.StripeError as e:
            return JsonResponse({
                'error': str(e.user_message)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'error': 'An unexpected error occurred. Please try again.'
            }, status=400)

    # GET request - render form
    AMOUNT_CHOICES = [
        (50, '$50'),
        (100, '$100'),
        (150, '$150'),
        (200, '$200'),
        (250, '$250'),
    ]

    context = {
        'AMOUNT_CHOICES': AMOUNT_CHOICES,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'pending_giftcard': pending_giftcard  # Add this to context
    }

    return render(request, 'giftcards/purchase.html', context)

@login_required
def confirm_purchase(request, card_id):
    gift_card = get_object_or_404(GiftCard, card_id=card_id, purchaser=request.user)

    if gift_card.status == 'active':
        messages.warning(request, 'This gift card has already been activated.')
        return redirect('giftcards:my_giftcards')

    try:
        payment_intent_id = request.GET.get('payment_intent')
        if not payment_intent_id:
            messages.error(request, 'No payment information provided.')
            return redirect('giftcards:purchase')

        # Verify payment with Stripe
        payment = stripe.PaymentIntent.retrieve(payment_intent_id)

        if payment.status == 'succeeded':
            # Update gift card status
            gift_card.status = 'active'
            gift_card.save()

            # Create transaction record
            GiftCardTransaction.objects.create(
                gift_card=gift_card,
                transaction_type='purchase',
                amount=gift_card.amount,
                user=request.user
            )
            # Create transaction record
            Transaction.objects.create(
                user=request.user,
                transaction_type='gift_card_purchase',
                amount=gift_card.amount,
                status='completed',
                payment_method='stripe',
                payment_id=payment_intent_id,
                reference_id=str(gift_card.card_number),
                description=f'Gift Card purchase for {gift_card.recipient_name}'
            )

            # Send confirmation emails
            try:
                send_giftcard_emails(gift_card)
                messages.success(request, 'Gift card purchased successfully! Confirmation emails have been sent.')
            except Exception as email_error:
                print(f"Error sending emails: {str(email_error)}")
                messages.success(request, 'Gift card purchased successfully! However, there was an issue sending confirmation emails.')

            return redirect('giftcards:my_giftcards')
        else:
            messages.error(request, 'Payment verification failed.')
            return redirect('giftcards:purchase')

    except stripe.error.StripeError as e:
        messages.error(request, f'Payment error: {str(e)}')
        return redirect('giftcards:purchase')
    except Exception as e:
        messages.error(request, f'Error confirming purchase: {str(e)}')
        return redirect('giftcards:purchase')
    except Exception as e:
        messages.error(request, f'Error confirming purchase: {str(e)}')
        return redirect('giftcards:purchase')


@login_required
def my_giftcards(request):
    purchased_cards = GiftCard.objects.filter(purchaser=request.user).order_by('-purchase_date')
    received_cards = GiftCard.objects.filter(recipient_email=request.user.email).order_by('-purchase_date')

    return render(request, 'giftcards/my_giftcards.html', {
        'purchased_cards': purchased_cards,
        'received_cards': received_cards
    })


# giftcards/views.py

@login_required
def redeem_giftcard(request):
    if request.method == 'POST':
        card_id = request.POST.get('card_id')
        amount = Decimal(request.POST.get('amount', 0))

        try:
            gift_card = get_object_or_404(GiftCard, card_id=card_id)

            if not gift_card.is_valid():
                messages.error(request, 'This gift card is invalid or expired.')
                return redirect('giftcards:my_giftcards')

            if amount > gift_card.balance:
                messages.error(request, 'Insufficient balance on gift card.')
                return redirect('giftcards:my_giftcards')

            # Process redemption
            gift_card.balance -= amount
            if gift_card.balance == 0:
                gift_card.status = 'redeemed'
                gift_card.redeemed_by = request.user
                gift_card.redeemed_date = timezone.now()
            gift_card.save()

            # Create transaction record
            Transaction.objects.create(
                user=request.user,
                transaction_type='giftcard_redemption',
                amount=amount,
                reference_id=str(gift_card.card_id),
                description=f'Gift Card redemption of ${amount}'
            )

            messages.success(request, f'Successfully redeemed ${amount} from gift card.')

        except Exception as e:
            messages.error(request, f'Error redeeming gift card: {str(e)}')

    return redirect('giftcards:my_giftcards')


def send_giftcard_emails(gift_card):
    """Send confirmation emails to recipient and restaurant"""
    context = {
        'gift_card': gift_card,
        'restaurant_name': 'Royal Nepal Restaurant',
        'restaurant_logo_url': settings.SITE_URL + '/static/img/logo.png' if hasattr(settings, 'SITE_URL') else None,
        'restaurant_address': 'Your Restaurant Address',
        'restaurant_phone': '+1 5589 55488 55'
    }

    # Send to recipient
    try:
        recipient_html = render_to_string('giftcards/emails/giftcard_recipient.html', context)
        recipient_text = strip_tags(recipient_html)

        send_mail(
            subject=f'Your {context["restaurant_name"]} Gift Card!',
            message=recipient_text,
            html_message=recipient_html,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[gift_card.recipient_email],
            fail_silently=False
        )
        print(f"Recipient email sent successfully to {gift_card.recipient_email}")
    except Exception as e:
        print(f"Error sending recipient email: {str(e)}")
        raise

    # Send to restaurant admin
    try:
        admin_html = render_to_string('giftcards/emails/giftcard_admin.html', context)
        admin_text = strip_tags(admin_html)

        send_mail(
            subject=f'New Gift Card Purchase - #{gift_card.card_number}',
            message=admin_text,
            html_message=admin_html,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.RESTAURANT_ORDER_EMAIL],
            fail_silently=False
        )
        print(f"Admin email sent successfully to {settings.RESTAURANT_ORDER_EMAIL}")
    except Exception as e:
        print(f"Error sending admin email: {str(e)}")
        raise

    # # Send confirmation to purchaser
    # try:
    #     purchaser_html = render_to_string('giftcards/emails/giftcard_recipient.html', context)
    #     purchaser_text = strip_tags(purchaser_html)
    #
    #     send_mail(
    #         subject=f'Gift Card Purchase Confirmation - {context["restaurant_name"]}',
    #         message=purchaser_text,
    #         html_message=purchaser_html,
    #         from_email=settings.DEFAULT_FROM_EMAIL,
    #         recipient_list=[gift_card.purchaser.email],
    #         fail_silently=False
    #     )
    #     print(f"Purchaser email sent successfully to {gift_card.purchaser.email}")
    # except Exception as e:
    #     print(f"Error sending purchaser email: {str(e)}")
    #     raise


# In views.py
@login_required
def complete_payment(request, card_id):
    gift_card = get_object_or_404(GiftCard, card_id=card_id, purchaser=request.user)

    if gift_card.status != 'pending':
        messages.error(request, 'This gift card does not require payment completion.')
        return redirect('giftcards:my_giftcards')

    # Store gift card data in session for use in purchase form
    request.session['pending_giftcard'] = {
        'card_id': str(gift_card.card_id),
        'amount': str(gift_card.amount),
        'recipient_name': gift_card.recipient_name,
        'recipient_email': gift_card.recipient_email,
        'message': gift_card.message
    }

    return redirect('giftcards:purchase')

@login_required
def validate_redeem(request, card_number):
    giftcard = get_object_or_404(GiftCard, card_number=card_number)
    return render(request, 'giftcards/validate_redeem.html', {'giftcard': giftcard})

@login_required
def validate_card(request, card_number):
    try:
        giftcard = GiftCard.objects.get(card_number=card_number)
        if giftcard.is_valid():
            return JsonResponse({
                'valid': True,
                'balance': float(giftcard.balance),
                'status': giftcard.status,
                'expiry_date': giftcard.expiry_date.strftime('%Y-%m-%d')
            })
        return JsonResponse({
            'valid': False,
            'message': 'Gift card is invalid, expired, or has no balance.'
        })
    except GiftCard.DoesNotExist:
        return JsonResponse({
            'valid': False,
            'message': 'Gift card not found.'
        })

@login_required
def redeem_card(request, card_number):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})

    try:
        data = json.loads(request.body)
        amount = Decimal(str(data.get('amount', 0)))
        giftcard = get_object_or_404(GiftCard, card_number=card_number)

        if not giftcard.is_valid():
            return JsonResponse({
                'success': False,
                'message': 'Gift card is invalid or expired.'
            })

        if amount > giftcard.balance:
            return JsonResponse({
                'success': False,
                'message': 'Insufficient balance.'
            })

        # Process redemption
        giftcard.balance -= amount
        if giftcard.balance == 0:
            giftcard.status = 'redeemed'
            giftcard.redeemed_by = request.user
            giftcard.redeemed_date = timezone.now()
        giftcard.save()

        # Create transaction record
        GiftCardTransaction.objects.create(
            gift_card=giftcard,
            transaction_type='redemption',
            amount=amount,
            user=request.user
        )

        return JsonResponse({
            'success': True,
            'new_balance': float(giftcard.balance)
        })

    except (ValueError, TypeError):
        return JsonResponse({
            'success': False,
            'message': 'Invalid amount specified.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })