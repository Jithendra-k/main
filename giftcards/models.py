# giftcards/models.py


from django.contrib.auth.models import User
from django.db import models
import uuid
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone


class GiftCard(models.Model):
    AMOUNT_CHOICES = [
        (Decimal('50.00'), '$50'),
        (Decimal('100.00'), '$100'),
        (Decimal('150.00'), '$150'),
        (Decimal('200.00'), '$200'),
        (Decimal('250.00'), '$250'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Payment Pending'),
        ('active', 'Active'),
        ('redeemed', 'Fully Redeemed'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled')
    ]

    card_number = models.PositiveIntegerField(unique=True)
    card_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    purchaser = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='purchased_giftcards_user'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    recipient_name = models.CharField(max_length=100)
    recipient_email = models.EmailField()
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    purchase_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    redeemed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='redeemed_giftcards_user'
    )
    redeemed_date = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:  # New gift card
            # Get the highest card_number and add 1
            last_card = GiftCard.objects.order_by('-card_number').first()
            self.card_number = (last_card.card_number + 1) if last_card else 1

            # Set initial balance equal to amount
            self.balance = self.amount

            # Set expiry date to 1 year from purchase
            self.expiry_date = timezone.now() + timezone.timedelta(days=365)

        super().save(*args, **kwargs)

    def is_valid(self):
        return (
                self.status == 'active' and
                self.expiry_date > timezone.now() and
                self.balance > 0
        )

    def mark_as_paid(self):
        if self.status == 'pending':
            self.status = 'active'
            self.save()

    class Meta:
        ordering = ['-purchase_date']

    def __str__(self):
        return f"Card #{self.card_number} - ${self.amount}"


class GiftCardTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('purchase', 'Purchase'),
        ('redemption', 'Redemption'),
        ('refund', 'Refund')
    ]

    gift_card = models.ForeignKey(GiftCard, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.gift_card.card_id}"

    class Meta:
        ordering = ['-date']



