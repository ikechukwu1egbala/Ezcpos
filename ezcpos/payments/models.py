from django.db import models
from django.conf import settings
from pos.models import Sale, SaleItem, Location


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
        related_name="payments",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
    )

    transaction_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default="pending",
    )

    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"Sale #{self.sale.id} - ₦{self.amount}"


class Refund(models.Model):
    REFUND_REASONS = (
        ("customer_return", "Customer Return"),
        ("wrong_sale", "Wrong Sale"),
        ("damaged_product", "Damaged Product"),
        ("duplicate_payment", "Duplicate Payment"),
        ("other", "Other"),
    )

    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="refunds",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    reason = models.CharField(
        max_length=30,
        choices=REFUND_REASONS,
    )

    reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="processed_refunds",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"Refund - Payment #{self.payment.id} - ₦{self.amount}"


class SalesReturn(models.Model):
    RETURN_REASONS = (
        ("customer_return", "Customer Return"),
        ("wrong_sale", "Wrong Sale"),
        ("damaged_product", "Damaged Product"),
        ("expired_product", "Expired Product"),
        ("other", "Other"),
    )

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="returns",
    )

    refund = models.ForeignKey(
        Refund,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sales_returns",
    )

    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sales_returns",
    )

    reason = models.CharField(
        max_length=30,
        choices=RETURN_REASONS,
    )

    reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="processed_sales_returns",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"Return - Sale #{self.sale.id}"


class SalesReturnItem(models.Model):
    sales_return = models.ForeignKey(
        SalesReturn,
        on_delete=models.CASCADE,
        related_name="items",
    )

    sale_item = models.ForeignKey(
        SaleItem,
        on_delete=models.PROTECT,
        related_name="return_items",
    )

    quantity = models.DecimalField(
        max_digits=18,
        decimal_places=6,
    )

    refund_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return (
            f"Return #{self.sales_return.id} - "
            f"SaleItem #{self.sale_item.id} - "
            f"{self.quantity}"
        )
