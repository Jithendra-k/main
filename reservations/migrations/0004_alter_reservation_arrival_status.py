# Generated by Django 4.2.17 on 2025-01-04 07:33

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "reservations",
            "0003_alter_reservation_options_reservation_arrival_status_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="reservation",
            name="arrival_status",
            field=models.CharField(
                choices=[
                    ("not_arrived", "Not yet Arrived"),
                    ("seated", "Seated"),
                    ("no_show", "No Show"),
                ],
                default="not_arrived",
                max_length=20,
            ),
        ),
    ]
