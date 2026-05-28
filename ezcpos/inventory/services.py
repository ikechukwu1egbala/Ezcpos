from .models import InventoryLog


def log_stock(product, change, reason):

    InventoryLog.objects.create(
        product=product,
        change=change,
        reason=reason
    )

