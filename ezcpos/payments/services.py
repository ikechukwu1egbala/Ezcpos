from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Sum

from .models import (
    Payment,
    Refund,
    SalesReturn,
    SalesReturnItem,
)


@transaction.atomic
def process_payment(
    sale,
    amount,
    method,
    user,
    reference=None,
):
    from pos.models import Sale

    sale = Sale.objects.select_for_update().get(
        pk=sale.pk
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
        raise ValueError("Invalid payment method.")

    completed_paid = (
        Payment.objects.filter(
            sale=sale,
            status="completed",
        ).aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    outstanding = (
        sale.total_amount - completed_paid
    )

    if outstanding <= Decimal("0.00"):
        raise ValueError(
            "This sale has already been fully paid."
        )

    if amount > outstanding:
        raise ValueError(
            "Payment exceeds outstanding balance. "
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
    payment = Payment.objects.select_for_update().get(
        pk=payment.pk
    )

    if payment.status not in [
        "completed",
        "refunded",
    ]:
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
        raise ValueError("Invalid refund reason.")

    already_refunded = (
        Refund.objects.filter(
            payment=payment
        ).aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    refundable_amount = (
        payment.amount - already_refunded
    )

    if refundable_amount <= Decimal("0.00"):
        raise ValueError(
            "This payment has already been fully refunded."
        )

    if amount > refundable_amount:
        raise ValueError(
            "Refund exceeds refundable amount. "
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


@transaction.atomic
def process_sales_return(
    sale,
    items,
    location,
    reason,
    user,
    refund=None,
    reference=None,
):
    from pos.models import (
        InventoryBalance,
        InventoryMovement,
        Location,
        SaleItem,
    )

    sale = sale.__class__.objects.select_for_update().get(
        pk=sale.pk
    )

    if not items:
        raise ValueError(
            "At least one returned item is required."
        )

    if location is None:
        location = (
            Location.objects.filter(
                is_active=True
            ).order_by("id").first()
        )

    if location is None:
        raise ValueError(
            "No active inventory location is available."
        )

    valid_reasons = {
        choice[0]
        for choice in SalesReturn.RETURN_REASONS
    }

    if reason not in valid_reasons:
        raise ValueError("Invalid return reason.")

    if refund is not None:
        refund = Refund.objects.select_for_update().get(
            pk=refund.pk
        )

        if refund.payment.sale_id != sale.id:
            raise ValueError(
                "Refund does not belong to this sale."
            )

    sales_return = SalesReturn.objects.create(
        sale=sale,
        refund=refund,
        location=location,
        reason=reason,
        reference=reference,
        processed_by=user,
    )

    for item in items:
        sale_item_id = item.get("sale_item")
        quantity = item.get("quantity")
        refund_amount = item.get(
            "refund_amount",
            Decimal("0.00"),
        )

        if not sale_item_id:
            raise ValueError(
                "Each returned item requires sale_item."
            )

        try:
            quantity = Decimal(str(quantity))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(
                "Invalid return quantity."
            )

        try:
            refund_amount = Decimal(
                str(refund_amount)
            )
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(
                "Invalid refund amount."
            )

        if quantity <= Decimal("0"):
            raise ValueError(
                "Return quantity must be greater than zero."
            )

        if refund_amount < Decimal("0"):
            raise ValueError(
                "Item refund amount cannot be negative."
            )

        sale_item = (
            SaleItem.objects
            .select_for_update()
            .select_related(
                "product",
                "product_unit",
            )
            .get(pk=sale_item_id)
        )

        if sale_item.sale_id != sale.id:
            raise ValueError(
                f"Sale item #{sale_item_id} "
                "does not belong to this sale."
            )

        already_returned = (
            SalesReturnItem.objects.filter(
                sale_item=sale_item
            ).aggregate(
                total=Sum("quantity")
            )["total"]
            or Decimal("0")
        )

        remaining_quantity = (
            sale_item.quantity - already_returned
        )

        if quantity > remaining_quantity:
            raise ValueError(
                f"Cannot return {quantity} units of "
                f"{sale_item.product.name}. "
                f"Only {remaining_quantity} remain "
                "available for return."
            )

        balance, _ = (
            InventoryBalance.objects
            .select_for_update()
            .get_or_create(
                product=sale_item.product,
                location=location,
                status="available",
                defaults={
                    "quantity": Decimal("0")
                },
            )
        )

        balance.quantity += quantity
        balance.save(
            update_fields=[
                "quantity",
                "updated_at",
            ]
        )

        InventoryMovement.objects.create(
            product=sale_item.product,
            location=location,
            movement_type="in",
            quantity=quantity,
            reason="Customer Return",
            reference=(
                f"RETURN-{sales_return.id}"
            ),
            created_by=user,
        )

        SalesReturnItem.objects.create(
            sales_return=sales_return,
            sale_item=sale_item,
            quantity=quantity,
            refund_amount=refund_amount,
        )

    return sales_return


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
