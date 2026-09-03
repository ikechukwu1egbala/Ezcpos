from decimal import Decimal

from django.conf import settings
from django.db import models


# ============================================================
# CUSTOMER
# ============================================================

class Customer(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name


# ============================================================
# CATEGORY
# ============================================================

class Category(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


# ============================================================
# PRODUCT
# ============================================================

class Product(models.Model):
    name = models.CharField(max_length=200)

    barcode = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    description = models.TextField(blank=True)

    recognition_enabled = models.BooleanField(
        default=True,
        help_text="Allow this product to be identified by camera/AI recognition.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ============================================================
# Add Product Image
# This allows us to have multiple photographs per product.
# ============================================================

class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )

    image = models.ImageField(
        upload_to="products/",
    )

    title = models.CharField(
        max_length=200,
        blank=True,
    )

    is_primary = models.BooleanField(
        default=False,
    )

    recognition_enabled = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-is_primary", "-created_at"]

    def __str__(self):
        return f"{self.product.name} image"


# ============================================================
# product identifier for AI use
# Add Product Identifier
# ============================================================

class ProductIdentifier(models.Model):

    IDENTIFIER_TYPES = (
        ("BARCODE", "Barcode"),
        ("QR", "QR Code"),
        ("SKU", "SKU"),
        ("AI_LABEL", "AI Label"),
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="identifiers",
    )

    identifier_type = models.CharField(
        max_length=20,
        choices=IDENTIFIER_TYPES,
    )

    value = models.CharField(
        max_length=200,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["identifier_type", "value"],
                name="unique_product_identifier",
            )
        ]

    def __str__(self):
        return f"{self.identifier_type}: {self.value}"


# ============================================================
# LOCATION
# Warehouse, store, branch, etc.
# ============================================================

class Location(models.Model):

    LOCATION_TYPES = (
        ("warehouse", "Warehouse"),
        ("store", "Store"),
    )

    name = models.CharField(max_length=200)

    location_type = models.CharField(
        max_length=20,
        choices=LOCATION_TYPES,
    )

    address = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_location_type_display()})"


# ============================================================
# PRODUCT UNIT
#
# Defines the user's unit convention for a product.
#
# Example:
#
# Peak:
# Carton -> 21 Rolls
# Roll   -> 10 Sachets
#
# Oil:
# Truck -> 1000 Gallons
# Gallon -> 15 Kegs
#
# The user defines the units.
# ============================================================

class ProductUnit(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="units",
    )

    name = models.CharField(
        max_length=100,
        help_text="Example: Carton, Roll, Sachet, Truck, Gallon, Keg",
    )

    symbol = models.CharField(
        max_length=30,
        blank=True,
        help_text="Example: ctn, roll, kg, gal",
    )

    # How many base units make one of this unit.
    #
    # Example:
    # Carton = 21 rolls
    # Roll = 1 roll
    #
    conversion_to_base = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal("1"),
    )

    is_base_unit = models.BooleanField(default=False)

    is_sellable = models.BooleanField(default=True)

    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.product.name} - {self.name}"


# ============================================================
# UNIT PRICE
#
# Allows each unit convention to have its own cost/selling price.
#
# Example:
#
# Carton:
# cost = ₦23,000
# sell = ₦23,500
#
# Roll:
# cost = ₦1,095
# sell = ₦1,200
# ============================================================

class ProductUnitPrice(models.Model):

    product_unit = models.OneToOneField(
        ProductUnit,
        on_delete=models.CASCADE,
        related_name="pricing",
    )

    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    allow_below_cost = models.BooleanField(
        default=False,
        help_text="Allow selling below cost as an incentive/reward.",
    )

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product_unit} - ₦{self.selling_price}"


# ============================================================
# INVENTORY BALANCE
#
# Stock belonging to a product at a particular location.
#
# We deliberately use DecimalField because quantities may be
# fractional.
#
# Example:
#
# Main Warehouse
# Product: Peak
# Full packs = 9
# Loose units = 21
#
# Total base units are calculated from the ProductUnit.
# ============================================================

class InventoryBalance(models.Model):

    STOCK_STATUS = (
        ("AVAILABLE", "Available"),
        ("RESERVED", "Reserved"),
        ("DAMAGED", "Damaged"),
        ("EXPIRED", "Expired"),
        ("IN_TRANSIT", "In Transit"),
        ("QUARANTINED", "Quarantined"),
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="inventory_balances",
    )

    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="inventory",
    )

    status = models.CharField(
        max_length=20,
        choices=STOCK_STATUS,
        default="AVAILABLE",
    )

    quantity = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal("0"),
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "location", "status"],
                name="unique_product_location_status",
            )
        ]

    def __str__(self):
        return (
            f"{self.product.name} - "
            f"{self.location.name} - "
            f"{self.status}: {self.quantity}"
        )


# ============================================================
# INVENTORY MOVEMENT
#
# Every stock increase/decrease/transfer should eventually
# create a movement record.
# ============================================================

class InventoryMovement(models.Model):

    MOVEMENT_TYPES = (
        ("IN", "Stock In"),
        ("OUT", "Stock Out"),
        ("TRANSFER", "Transfer"),
        ("ADJUSTMENT", "Adjustment"),
        ("RESERVE", "Reserve"),
        ("RELEASE", "Release"),
        ("DAMAGE", "Damage"),
        ("EXPIRE", "Expire"),
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="inventory_movements",
    )

    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="inventory_movements",
    )

    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPES,
    )

    quantity = models.DecimalField(
        max_digits=18,
        decimal_places=6,
    )

    reason = models.CharField(
        max_length=255,
        blank=True,
    )

    reference = models.CharField(
        max_length=100,
        blank=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return (
            f"{self.product.name} - "
            f"{self.movement_type} - "
            f"{self.quantity}"
        )


# ============================================================
# SALE
# ============================================================

class Sale(models.Model):

    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"Sale #{self.id}"


# ============================================================
# SALE ITEM
#
# Quantity is Decimal because the user may sell:
#
# 1
# 0.5
# 0.25
# 0.333333
# etc.
#
# The actual unit being sold is stored separately.
# ============================================================

class SaleItem(models.Model):

    sale = models.ForeignKey(
        Sale,
        related_name="items",
        on_delete=models.CASCADE,
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
    )

    product_unit = models.ForeignKey(
        ProductUnit,
        on_delete=models.PROTECT,
        related_name="sale_items",
        null=True,
        blank=True,
    )

    quantity = models.DecimalField(
        max_digits=18,
        decimal_places=6,
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    def get_total(self):
        return self.quantity * self.price

    def __str__(self):
        return (
            f"{self.product.name} "
            f"x {self.quantity}"
        )


# ============================================================
# OLD INVENTORY MODEL
#
# Kept temporarily for migration compatibility.
# We will stop using this as the main inventory system.
# ============================================================

class Inventory(models.Model):

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
    )

    quantity = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=Decimal("0"),
    )

    last_updated = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.product.name