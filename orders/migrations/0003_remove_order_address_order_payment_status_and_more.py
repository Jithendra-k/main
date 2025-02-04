# Generated by Django 4.2.17 on 2024-12-31 04:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0002_order_payment_method"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="order",
            name="address",
        ),
        migrations.AddField(
            model_name="order",
            name="payment_status",
            field=models.CharField(
                choices=[("pending", "Pending"), ("paid", "Paid")],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="pickup_time",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="order",
            name="payment_method",
            field=models.CharField(
                choices=[
                    ("in_store", "Pay at Pickup"),
                    ("card", "Credit/Debit Card"),
                    ("apple_pay", "Apple Pay"),
                    ("paypal", "PayPal"),
                ],
                default="in_store",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Order Received"),
                    ("in_progress", "In Progress"),
                    ("ready", "Ready for Pickup"),
                    ("completed", "Completed"),
                    ("cancelled", "Cancelled"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]
