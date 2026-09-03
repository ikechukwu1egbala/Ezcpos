from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from .models import Payment


@transaction.atomic
def process_payment(
    sale,
    amount,
    method,
    user,
    reference=None,
):
    """
    Process a payment against a sale.

    Supports:
    - Full payment
    - Part payment
    - Split payments
    - Customer credit
    """

    amount = Decimal(str(amount))

    if amount <= 0:
        raise ValueError(
            "Payment amount must be greater than zero."
        )

    # Lock the sale's payment records while processing.
    completed_paid = (
        Payment.objects
        .select_for_update()
        .filter(
            sale=sale,
            status="completed",
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    outstanding = (
        sale.total_amount - completed_paid
    )

    if outstanding <= 0:
        raise ValueError(
            "This sale has already been fully paid."
        )

    if amount > outstanding:
        raise ValueError(
            f"Payment exceeds outstanding balance. "
            f"Outstanding balance is ₦{outstanding}."
        )

    payment = Payment.objects.create(
        sale=sale,
        amount=amount,
        payment_method=method,
        transaction_reference=reference,
        processed_by=user,
        status="completed",
    )

    return payment


@transaction.atomic
def refund_payment(
    payment,
    user,
):
    """
    Refund a completed payment.
    """

    if payment.status != "completed":
        raise ValueError(
            "Only completed payments can be refunded."
        )

    payment.status = "refunded"

    payment.save(
        update_fields=["status"]
    )

    return payment


# Backward-compatible alias.
#
# This allows existing code using record_payment()
# to continue working while the API uses process_payment().

def record_payment(
    sale,
    amount,
    payment_method,
    processed_by,
    transaction_reference=None,
):

    return process_payment(
        sale=sale,
        amount=amount,
        method=payment_method,
        user=processed_by,
        reference=transaction_reference,
    )
    