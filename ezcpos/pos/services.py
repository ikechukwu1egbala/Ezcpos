from decimal import Decimal

from django.db import transaction

from .models import (
    Product,
    ProductUnit,
    Sale,
    SaleItem,
    Location,
    InventoryBalance,
    InventoryMovement,
)


@transaction.atomic
def create_sale(
    items,
    cashier,
    customer=None,
    location=None,
    discount=Decimal("0.00"),
):
    if not items:
        raise ValueError("At least one sale item is required.")

    if location is None:
        location = (
            Location.objects
            .filter(is_active=True)
            .order_by("id")
            .first()
        )

    if location is None:
        raise ValueError("No active inventory location is available.")

    try:
        discount = Decimal(str(discount))
    except Exception:
        raise ValueError("Invalid discount amount.")

    if discount < Decimal("0.00"):
        raise ValueError("Discount cannot be negative.")

    prepared_items = []
    subtotal = Decimal("0.00")

    for item in items:
        product_id = item.get("product")
        quantity = item.get("quantity")
        product_unit_id = item.get("product_unit")

        if not product_id:
            raise ValueError("Each item requires a product.")

        try:
            quantity = Decimal(str(quantity))
        except Exception:
            raise ValueError("Invalid sale quantity.")

        if quantity <= Decimal("0"):
            raise ValueError("Sale quantity must be greater than zero.")

        product = (
            Product.objects
            .select_for_update()
            .get(pk=product_id)
        )

        product_unit = None
        inventory_quantity = quantity

        if product_unit_id:
            product_unit = (
                ProductUnit.objects
                .select_related("pricing")
                .get(
                    pk=product_unit_id,
                    product=product,
                )
            )

            if not hasattr(product_unit, "pricing"):
                raise ValueError(
                    f"No selling price configured for {product.name}."
                )

            price = product_unit.pricing.selling_price

            inventory_quantity = (
                quantity * product_unit.conversion_to_base
            )

        else:
            price = product.price

        if price is None:
            raise ValueError(
                f"No selling price configured for {product.name}."
            )

        line_total = quantity * price
        subtotal += line_total

        prepared_items.append(
            {
                "product": product,
                "product_unit": product_unit,
                "quantity": quantity,
                "inventory_quantity": inventory_quantity,
                "price": price,
            }
        )

    if discount > subtotal:
        raise ValueError(
            f"Discount cannot exceed subtotal of ₦{subtotal}."
        )

    total_amount = subtotal - discount

    sale = Sale.objects.create(
        cashier=cashier,
        customer=customer,
        subtotal=subtotal,
        discount=discount,
        total_amount=total_amount,
    )

    for prepared in prepared_items:
        product = prepared["product"]
        product_unit = prepared["product_unit"]
        quantity = prepared["quantity"]
        inventory_quantity = prepared["inventory_quantity"]
        price = prepared["price"]

        balance = (
            InventoryBalance.objects
            .select_for_update()
            .filter(
                product=product,
                location=location,
                status="available",
            )
            .first()
        )

        if balance is None:
            raise ValueError(
                f"No inventory balance exists for {product.name} "
                f"at {location.name}."
            )

        if balance.quantity < inventory_quantity:
            raise ValueError(
                f"Insufficient stock for {product.name}. "
                f"Available: {balance.quantity}, "
                f"requested: {inventory_quantity}."
            )

        SaleItem.objects.create(
            sale=sale,
            product=product,
            product_unit=product_unit,
            quantity=quantity,
            price=price,
        )

        balance.quantity -= inventory_quantity
        balance.save(
            update_fields=[
                "quantity",
                "updated_at",
            ]
        )

        InventoryMovement.objects.create(
            product=product,
            location=location,
            movement_type="out",
            quantity=inventory_quantity,
            reason="Sale",
            reference=f"SALE-{sale.id}",
            created_by=cashier,
        )

    return sale


def reduce_stock(
    product,
    quantity,
    location,
    user,
    reason="Manual Stock Reduction",
    reference=None,
):
    with transaction.atomic():
        balance = (
            InventoryBalance.objects
            .select_for_update()
            .filter(
                product=product,
                location=location,
                status="available",
            )
            .first()
        )

        if balance is None:
            raise ValueError(
                f"No inventory balance exists for {product.name}."
            )

        if quantity <= 0:
            raise ValueError(
                "Quantity must be greater than zero."
            )

        if balance.quantity < quantity:
            raise ValueError(
                f"Insufficient stock for {product.name}."
            )

        balance.quantity -= quantity

        balance.save(
            update_fields=[
                "quantity",
                "updated_at",
            ]
        )

        InventoryMovement.objects.create(
            product=product,
            location=location,
            movement_type="out",
            quantity=quantity,
            reason=reason,
            reference=reference,
            created_by=user,
        )

        return balance
