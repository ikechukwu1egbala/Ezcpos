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
def create_sale(items, cashier, customer=None, location=None):
    """
    Create a sale and reduce inventory atomically.

    Example:
    items = [
        {
            "product_id": 1,
            "quantity": 2,
        },
        {
            "product_id": 3,
            "quantity": 1,
            "product_unit_id": 5,
        },
    ]

    If a product_unit is supplied, its selling price is used.
    Otherwise, the product's legacy price field is used.

    Inventory is reduced from the selected location.
    """

    if not items:
        raise ValueError("A sale must contain at least one item.")

    # ---------------------------------------------------------
    # Find the location
    # ---------------------------------------------------------
    if location is None:
        location = Location.objects.filter(
            is_active=True
        ).order_by("id").first()

    if location is None:
        raise ValueError(
            "No active inventory location exists. "
            "Create an active store or warehouse first."
        )

    total_amount = Decimal("0.00")
    sale_items = []

    # ---------------------------------------------------------
    # Validate products and inventory
    # ---------------------------------------------------------
    for item in items:
        product_id = item.get("product_id")
        quantity = Decimal(str(item.get("quantity", 0)))

        if not product_id:
            raise ValueError("Each sale item must have a product_id.")

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        product = Product.objects.select_for_update().get(
            id=product_id
        )

        # -----------------------------------------------------
        # Determine selling unit and price
        # -----------------------------------------------------
        product_unit_id = item.get("product_unit_id")
        product_unit = None

        if product_unit_id:
            product_unit = ProductUnit.objects.select_related(
                "pricing"
            ).get(
                id=product_unit_id,
                product=product,
            )

            if not hasattr(product_unit, "pricing"):
                raise ValueError(
                    f"No price has been configured for "
                    f"{product.name} ({product_unit.name})."
                )

            price = product_unit.pricing.selling_price

            if price is None:
                raise ValueError(
                    f"No selling price has been configured for "
                    f"{product.name} ({product_unit.name})."
                )

            # Convert the sold unit quantity into base inventory quantity.
            inventory_quantity = (
                quantity * product_unit.conversion_to_base
            )

        else:
            price = product.price
            inventory_quantity = quantity

        # -----------------------------------------------------
        # Lock the inventory balance
        # -----------------------------------------------------
        inventory = InventoryBalance.objects.select_for_update().filter(
            product=product,
            location=location,
            status="available",
        ).first()

        if inventory is None:
            raise ValueError(
                f"No available inventory record exists for "
                f"{product.name} at {location.name}."
            )

        if inventory.quantity < inventory_quantity:
            raise ValueError(
                f"Not enough stock for {product.name}. "
                f"Available: {inventory.quantity}, "
                f"requested: {inventory_quantity}."
            )

        subtotal = price * quantity
        total_amount += subtotal

        sale_items.append(
            {
                "product": product,
                "product_unit": product_unit,
                "quantity": quantity,
                "price": price,
                "inventory": inventory,
                "inventory_quantity": inventory_quantity,
            }
        )

    # ---------------------------------------------------------
    # Create the sale
    # ---------------------------------------------------------
    sale = Sale.objects.create(
        cashier=cashier,
        customer=customer,
        total_amount=total_amount,
    )

    # ---------------------------------------------------------
    # Create sale items and reduce inventory
    # ---------------------------------------------------------
    for item in sale_items:
        SaleItem.objects.create(
            sale=sale,
            product=item["product"],
            product_unit=item["product_unit"],
            quantity=item["quantity"],
            price=item["price"],
        )

        inventory = item["inventory"]
        inventory.quantity -= item["inventory_quantity"]
        inventory.save(update_fields=["quantity", "updated_at"])

        InventoryMovement.objects.create(
            product=item["product"],
            location=location,
            movement_type="out",
            quantity=item["inventory_quantity"],
            reason="Sale",
            reference=f"SALE-{sale.id}",
            created_by=cashier,
        )

    return sale


def reduce_stock(product_id, quantity, location=None, user=None):
    """
    Reduce available inventory for a product.

    This helper is kept for compatibility with older code.
    New sales should normally use create_sale().
    """

    quantity = Decimal(str(quantity))

    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")

    if location is None:
        location = Location.objects.filter(
            is_active=True
        ).order_by("id").first()

    if location is None:
        raise ValueError("No active inventory location exists.")

    with transaction.atomic():
        inventory = InventoryBalance.objects.select_for_update().filter(
            product_id=product_id,
            location=location,
            status="available",
        ).first()

        if inventory is None:
            raise ValueError(
                "No available inventory record exists for this product."
            )

        if inventory.quantity < quantity:
            raise ValueError(
                f"Not enough stock. Available: {inventory.quantity}, "
                f"requested: {quantity}."
            )

        inventory.quantity -= quantity
        inventory.save(update_fields=["quantity", "updated_at"])

        InventoryMovement.objects.create(
            product_id=product_id,
            location=location,
            movement_type="out",
            quantity=quantity,
            reason="Stock reduction",
            created_by=user,
        )

        return inventory
