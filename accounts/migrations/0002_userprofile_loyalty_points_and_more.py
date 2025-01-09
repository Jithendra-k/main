# Generated by Django 4.2.17 on 2025-01-04 07:33

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="loyalty_points",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="rewards_balance",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
