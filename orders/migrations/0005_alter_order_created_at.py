# Generated by Django 4.2.17 on 2024-12-31 09:17

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0004_order_tip_amount"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="created_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
