# Generated by Django 4.2.17 on 2025-01-02 06:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reservations", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="eventbooking",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending Payment"),
                    ("confirmed", "Confirmed"),
                    ("cancelled", "Cancelled"),
                ],
                default="confirmed",
                max_length=20,
            ),
        ),
    ]
