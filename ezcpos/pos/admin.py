from django.contrib import admin

from .models import (
    Customer,
    Category,
    Product,
    ProductImage,
    ProductIdentifier,
    Location,
    ProductUnit,
    ProductUnitPrice,
    InventoryBalance,
    InventoryMovement,
    Sale,
    SaleItem,
)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "phone",
        "address",
    )
    search_fields = (
        "name",
        "phone",
        "address",
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "barcode",
        "price",
        "recognition_enabled",
        "created_at",
    )
    list_filter = (
        "category",
        "recognition_enabled",
    )
    search_fields = (
        "name",
        "barcode",
        "description",
    )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "title",
        "is_primary",
        "recognition_enabled",
        "created_at",
    )
    list_filter = (
        "is_primary",
        "recognition_enabled",
    )
    search_fields = (
        "product__name",
        "title",
    )


@admin.register(ProductIdentifier)
class ProductIdentifierAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "identifier_type",
        "value",
        "is_active",
    )
    list_filter = (
        "identifier_type",
        "is_active",
    )
    search_fields = (
        "value",
        "product__name",
    )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "location_type",
        "address",
        "is_active",
        "created_at",
    )
    list_filter = (
        "location_type",
        "is_active",
    )
    search_fields = (
        "name",
        "address",
    )


@admin.register(ProductUnit)
class ProductUnitAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "name",
        "symbol",
        "conversion_to_base",
        "is_base_unit",
        "is_sellable",
        "sort_order",
    )
    list_filter = (
        "is_base_unit",
        "is_sellable",
    )
    search_fields = (
        "product__name",
        "name",
        "symbol",
    )


@admin.register(ProductUnitPrice)
class ProductUnitPriceAdmin(admin.ModelAdmin):
    list_display = (
        "product_unit",
        "cost_price",
        "selling_price",
        "allow_below_cost",
        "updated_at",
    )
    list_filter = (
        "allow_below_cost",
    )
    search_fields = (
        "product_unit__product__name",
        "product_unit__name",
    )


@admin.register(InventoryBalance)
class InventoryBalanceAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "location",
        "status",
        "quantity",
    )
    list_filter = (
        "location",
        "status",
    )
    search_fields = (
        "product__name",
        "location__name",
    )


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "location",
        "movement_type",
        "quantity",
        "reason",
        "reference",
        "created_by",
        "created_at",
    )
    list_filter = (
        "movement_type",
        "location",
    )
    search_fields = (
        "product__name",
        "location__name",
        "reason",
        "reference",
    )


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "cashier",
        "customer",
        "subtotal",
        "discount",
        "total_amount",
        "created_at",
    )
    list_filter = (
        "cashier",
        "created_at",
    )
    search_fields = (
        "cashier__username",
        "customer__name",
    )


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = (
        "sale",
        "product",
        "product_unit",
        "quantity",
        "price",
    )
    search_fields = (
        "product__name",
    )
