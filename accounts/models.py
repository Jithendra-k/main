from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    loyalty_points = models.IntegerField(default=0)
    rewards_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.user.username

    def calculate_rewards(self, order_amount):
        """Calculate and add loyalty points based on order amount
        $1 = 10 points, 1000 points = $5 reward
        """
        points_earned = int(order_amount * 10)  # $1 = 10 points
        self.loyalty_points += points_earned

        # Convert points to rewards when they reach 1000
        while self.loyalty_points >= 1000:
            # Convert 1000 points to $5 reward
            self.loyalty_points -= 1000
            self.rewards_balance += Decimal('5.00')

        self.save(update_fields=['loyalty_points', 'rewards_balance'])
        return points_earned

    def use_rewards(self, amount):
        """Use available rewards for payment"""
        amount = Decimal(str(amount))
        if amount <= self.rewards_balance:
            self.rewards_balance -= amount
            self.rewards_balance = Decimal(str(round(self.rewards_balance, 2)))
            self.save(update_fields=['rewards_balance'])
            return True
        return False


# Remove the signal receivers and replace with a method
def get_or_create_profile(user):
    """
    Ensures a UserProfile is created for a given user
    """
    profile, created = UserProfile.objects.get_or_create(user=user)
    return profile

# accounts/models.py

# accounts/models.py

from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class Transaction(models.Model):
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('refunded', 'Refunded'),
        ('failed', 'Failed'),
        ('pending', 'Pending')
    ]

    PAYMENT_METHOD_CHOICES = [
        ('stripe', 'Credit Card'),
        ('apple_pay', 'Apple Pay'),
        ('paypal', 'PayPal'),
        ('in_store', 'Pay at Pickup'),
    ]
    TRANSACTION_TYPES = [
        ('order', 'Order Payment'),
        ('refund', 'Refund'),
        ('giftcard_purchase', 'Gift Card Purchase'),
        ('giftcard_redemption', 'Gift Card Redemption')
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)  # e.g., 'order', 'refund', 'gift_card'
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES,
        default='in_store'  # Default to in-store payment
    )
    payment_id = models.CharField(max_length=255, blank=True, null=True)  # Optional for in-store payments
    reference_id = models.CharField(max_length=100, blank=True)  # Order ID or other reference
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    refunded_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    refund_reason = models.TextField(blank=True)
    refunded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='refunds_processed'
    )
    refunded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} ({self.status})"

    def can_be_refunded(self):
        """Only online payments can be refunded through the system"""
        return (
                self.status == 'completed' and
                self.refunded_amount < self.amount and
                self.payment_method in ['stripe', 'apple_pay', 'paypal'] and
                self.payment_id is not None  # Must have a payment ID to refund
        )

    def save(self, *args, **kwargs):
        if not self.reference_id:
            if self.transaction_type == 'order':
                self.reference_id = f"ORD-{self.id}"
            elif self.transaction_type == 'gift_card_purchase':
                self.reference_id = f"GC-{self.id}"
            elif self.transaction_type == 'refund':
                self.reference_id = f"REF-{self.id}"
        super().save(*args, **kwargs)


