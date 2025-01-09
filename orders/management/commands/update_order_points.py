from django.core.management.base import BaseCommand
from orders.models import Order
from decimal import Decimal


class Command(BaseCommand):
    help = 'Update points earned for existing orders'

    def handle(self, *args, **kwargs):
        orders = Order.objects.all()
        updated_count = 0

        for order in orders:
            # Calculate points based on total amount
            points = int((order.total_amount / Decimal('100.00')) * 1000)

            # Update the order
            order.points_earned = points
            order.save(update_fields=['points_earned'])

            updated_count += 1
            self.stdout.write(f'Updated Order #{order.id}: ${order.total_amount} = {points} points')

        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} orders'))