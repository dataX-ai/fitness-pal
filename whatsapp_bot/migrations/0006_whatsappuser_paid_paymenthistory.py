# Generated by Django 5.0 on 2024-12-30 15:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("whatsapp_bot", "0005_rawmessage_processed_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="whatsappuser",
            name="paid",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="PaymentHistory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("subscription_id", models.CharField(max_length=255)),
                ("order_id", models.CharField(max_length=255)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("success", "Success"),
                            ("failed", "Failed"),
                            ("pending", "Pending"),
                        ],
                        max_length=20,
                    ),
                ),
                ("payment_time", models.DateTimeField()),
                ("payment_details", models.JSONField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payments",
                        to="whatsapp_bot.whatsappuser",
                    ),
                ),
            ],
        ),
    ]
