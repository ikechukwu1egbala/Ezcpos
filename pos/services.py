from django.db import transaction
from .models import Product, Sale, SaleItem


@transaction.atomic
def create_sale(items, cashier, customer=None, payment_method="cash"):
    """
    items example:
    [
        {"product_id": 1, "quantity": 2},
        {"product_id": 3, "quantity": 1}
    ]
    """

    total_amount = 0
    sale_items = []

    for item in items:
        product = Product.objects.select_for_update().get(id=item["product_id"])
        quantity = item["quantity"]

        if product.stock < quantity:
            raise ValueError(f"Not enough stock for {product.name}")

        price = product.price
        subtotal = price * quantity

        total_amount += subtotal

        # deduct stock
        product.stock -= quantity
        product.save()

        sale_items.append({
            "product": product,
            "quantity": quantity,
            "price": price,
            "subtotal": subtotal
        })

    sale = Sale.objects.create(
        cashier=cashier,
        customer=customer,
        total_amount=total_amount,
        payment_method=payment_method
    )

    for item in sale_items:
        SaleItem.objects.create(
            sale=sale,
            product=item["product"],
            quantity=item["quantity"],
            price=item["price"],
            subtotal=item["subtotal"]
        )

    return sale

def reduce_stock(product_id, quantity):
    product = Product.objects.get(id=product_id)
    product.stock -= quantity
    product.save()