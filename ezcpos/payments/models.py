from django.db import models
from django.conf import settings
from pos.models import Sale


class Payment(models.Model):

    PAYMENT_METHODS = (
        ("cash", "Cash"),
        ("card", "Card"),
        ("transfer", "Bank Transfer"),
        ("pos", "POS Terminal"),
    )

    PAYMENT_STATUS = (
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    )

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS
    )

    transaction_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default="pending"
    )

    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sale.receipt_number} - {self.amount}"