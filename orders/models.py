# orders/models.py
from django.db import models
from django.contrib.auth.models import User
from menu.models import MenuItem, ItemChoice, ItemAddon
from decimal import Decimal
from django.utils.timezone import now
from django.utils import timezone



class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Order Received'),
        ('in_progress', 'In Progress'),
        ('ready', 'Ready for Pickup'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]

    PAYMENT_CHOICES = [
        ('in_store', 'Pay at Pickup'),
        ('card', 'Credit/Debit Card'),
        ('apple_pay', 'Apple Pay'),
        ('paypal', 'PayPal')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    pickup_time = models.DateTimeField(null=True, blank=True)  # Optional pickup time
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='in_store')
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    ], default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    special_instructions = models.TextField(blank=True, null=True)
    tip_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    rewards_used = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)  # This will now include tip
    points_earned = models.IntegerField(default=0)
    transaction = models.OneToOneField(
        'accounts.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order'
    )

    def get_transaction_status(self):
        if self.transaction:
            return self.transaction.get_status_display()
        return 'No Transaction'

    def update_customer_rewards(self):
        """Update customer's loyalty points and rewards after order completion"""
        if self.user and self.status == 'completed' and not hasattr(self, '_rewards_processed'):
            self._rewards_processed = True
            actual_paid = self.total_amount - (self.rewards_used or Decimal('0.00'))

            # Update user's profile and convert points if necessary
            profile = self.user.profile
            points_earned = profile.calculate_rewards(actual_paid)

            # Update order points
            self.points_earned = points_earned
            self.save(update_fields=['points_earned'], update_rewards=False)

    def save(self, *args, **kwargs):
        update_rewards = kwargs.pop('update_rewards', True)
        is_new = not self.pk

        # Calculate points only for new orders
        if is_new:
            actual_paid = self.total_amount - (self.rewards_used or Decimal('0.00'))
            self.points_earned = int(actual_paid * 10)

        super().save(*args, **kwargs)

        # Only process rewards once when order is completed
        if update_rewards and self.status == 'completed' and not is_new:
            self.update_customer_rewards()

    def get_points_earned(self):
        """Get points earned for this order"""
        return self.points_earned or int((self.total_amount / Decimal('100.00')) * 1000)


    def apply_rewards(self):
        """Apply rewards and update user's balance"""
        if self.user:
            profile = self.user.profile
            # Verify user has enough rewards
            if profile.rewards_balance >= self.rewards_used:
                # Deduct rewards from user's balance
                profile.rewards_balance -= self.rewards_used
                profile.save()
                # Adjust total amount
                self.total_amount -= self.rewards_used
                self.save()
                return True
        return False

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

    def calculate_subtotal(self):
        """Calculate subtotal before tax and tip"""
        return sum(item.get_cost() for item in self.items.all())

    def calculate_tax(self, rate=Decimal('0.13')):
        """Calculate tax based on subtotal"""
        return round(self.calculate_subtotal() * rate, 2)

    def calculate_total_with_tip(self):
        """Calculate total including subtotal, tax, and tip"""
        subtotal = self.calculate_subtotal()
        tax = self.calculate_tax()
        return subtotal + tax + self.tip_amount

    def get_estimated_pickup_time(self):
        if self.pickup_time:
            return self.pickup_time.strftime('%I:%M %p')
        return "20-30 minutes from order confirmation"

    def get_total_with_tip(self):
        return self.total_amount + self.tip_amount


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    choice = models.ForeignKey(ItemChoice, null=True, blank=True, on_delete=models.SET_NULL)
    addons = models.ManyToManyField(ItemAddon, blank=True)
    special_instructions = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} in Order #{self.order.id}"

    def get_cost(self):
        total = self.price * self.quantity
        if self.choice:
            total += self.choice.price_adjustment * self.quantity  # Multiply by quantity
        if self.addons.exists():  # Check if there are any addons
            addon_total = sum(addon.price for addon in self.addons.all())
            total += addon_total * self.quantity  # Multiply total addons price by quantity
        return total


