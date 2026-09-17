from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Sum

from .models import Payment, Refund


@transaction.atomic
def process_payment(
    sale,
    amount,
    method,
    user,
    reference=None,
):
    from pos.models import Sale

    sale = (
        Sale.objects
        .select_for_update()
        .get(pk=sale.pk)
    )

    try:
        amount = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Invalid payment amount.")

    if amount <= Decimal("0.00"):
        raise ValueError(
            "Payment amount must be greater than zero."
        )

    valid_methods = {
        choice[0]
        for choice in Payment.PAYMENT_METHODS
    }

    if method not in valid_methods:
        raise ValueError(
            "Invalid payment method."
        )

    completed_paid = (
        Payment.objects
        .filter(
            sale=sale,
            status="completed",
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    outstanding = sale.total_amount - completed_paid

    if outstanding <= Decimal("0.00"):
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
    amount,
    reason,
    user,
    reference=None,
):
    payment = (
        Payment.objects
        .select_for_update()
        .get(pk=payment.pk)
    )

    if payment.status not in ["completed", "refunded"]:
        raise ValueError(
            "Only completed payments can be refunded."
        )

    try:
        amount = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Invalid refund amount.")

    if amount <= Decimal("0.00"):
        raise ValueError(
            "Refund amount must be greater than zero."
        )

    valid_reasons = {
        choice[0]
        for choice in Refund.REFUND_REASONS
    }

    if reason not in valid_reasons:
        raise ValueError(
            "Invalid refund reason."
        )

    already_refunded = (
        Refund.objects
        .filter(payment=payment)
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    refundable_amount = payment.amount - already_refunded

    if refundable_amount <= Decimal("0.00"):
        raise ValueError(
            "This payment has already been fully refunded."
        )

    if amount > refundable_amount:
        raise ValueError(
            f"Refund exceeds refundable amount. "
            f"Refundable amount is ₦{refundable_amount}."
        )

    refund = Refund.objects.create(
        payment=payment,
        amount=amount,
        reason=reason,
        reference=reference,
        processed_by=user,
    )

    new_total_refunded = (
        already_refunded + amount
    )

    if new_total_refunded >= payment.amount:
        payment.status = "refunded"
        payment.save(
            update_fields=["status"]
        )

    return refund


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
