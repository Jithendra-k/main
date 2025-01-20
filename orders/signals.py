# orders/signals.py
from decimal import Decimal

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order


@receiver(post_save, sender=Order)
def handle_order_completion(sender, instance, created, **kwargs):
    if not created and instance.status == 'completed' and not getattr(instance, '_signal_processed', False):
        instance._signal_processed = True
        instance.update_customer_rewards()