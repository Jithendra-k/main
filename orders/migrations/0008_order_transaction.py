# Generated by Django 4.2.17 on 2025-01-08 01:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_alter_transaction_options_and_more"),
        ("orders", "0007_order_points_earned"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="transaction",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="order",
                to="accounts.transaction",
            ),
        ),
    ]
