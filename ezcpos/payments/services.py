from django.db import transaction
from decimal import Decimal
from .models import Payment


@transaction.atomic
def process_payment(sale, amount, method, user, reference=None):

    amount = Decimal(amount)

    if amount <= 0:
        raise ValueError("Payment amount must be greater than zero")

    total_paid = sum(p.amount for p in sale.payments.all())
    remaining = sale.total_amount - total_paid

    if amount > remaining:
        raise ValueError("Payment exceeds remaining balance")

    payment = Payment.objects.create(
        sale=sale,
        amount=amount,
        payment_method=method,
        transaction_reference=reference,
        status="completed",
        processed_by=user,
    )

    total_paid += amount

    if total_paid >= sale.total_amount:
        sale.payment_status = "paid"
        sale.save()

    return payment

@transaction.atomic
def refund_payment(payment, user):

    if payment.status != "completed":
        raise ValueError("Only completed payments can be refunded")

    payment.status = "refunded"
    payment.save()

    sale = payment.sale

    total_paid = sum(
        p.amount for p in sale.payments.filter(status="completed")
    )

    if total_paid < sale.total_amount:
        sale.payment_status = "partial"
        sale.save()

    return payment
    