from rest_framework import serializers

from .models import (
    Product,
    Category,
    Customer,
    Sale,
    SaleItem,
    ProductImage,
    ProductIdentifier,
    ProductUnit,
    ProductUnitPrice,
    Location,
    InventoryBalance,
    InventoryMovement,
)


# ============================================================
# CATEGORY
# ============================================================

class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = "__all__"


# ============================================================
# PRODUCT IMAGE
# ============================================================

class ProductImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductImage
        fields = "__all__"

        read_only_fields = [
            "id",
            "created_at",
        ]


# ============================================================
# PRODUCT IDENTIFIER
# ============================================================

class ProductIdentifierSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductIdentifier
        fields = "__all__"

        read_only_fields = [
            "id",
            "created_at",
        ]


# ============================================================
# PRODUCT UNIT PRICE
# ============================================================

class ProductUnitPriceSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductUnitPrice
        fields = "__all__"

        read_only_fields = [
            "id",
            "updated_at",
        ]

    def validate(self, attrs):

        cost = attrs.get("cost_price")
        selling = attrs.get("selling_price")
        allow_below_cost = attrs.get(
            "allow_below_cost",
            False,
        )

        if (
            cost is not None
            and selling is not None
            and selling < cost
            and not allow_below_cost
        ):
            raise serializers.ValidationError(
                {
                    "selling_price": (
                        "Selling price cannot be below cost price "
                        "unless below-cost selling is explicitly allowed."
                    )
                }
            )

        return attrs


# ============================================================
# PRODUCT UNIT
# ============================================================

class ProductUnitSerializer(serializers.ModelSerializer):

    pricing = ProductUnitPriceSerializer(
        read_only=True
    )

    class Meta:
        model = ProductUnit
        fields = "__all__"

        read_only_fields = [
            "id",
        ]

    def validate_conversion_to_base(self, value):

        if value <= 0:
            raise serializers.ValidationError(
                "Conversion must be greater than zero."
            )

        return value


# ============================================================
# PRODUCT
# ============================================================

class ProductSerializer(serializers.ModelSerializer):

    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    images = ProductImageSerializer(
        many=True,
        read_only=True,
    )

    identifiers = ProductIdentifierSerializer(
        many=True,
        read_only=True,
    )

    units = ProductUnitSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Product
        fields = "__all__"

        read_only_fields = [
            "id",
            "created_at",
        ]


# ============================================================
# CUSTOMER
# ============================================================

class CustomerSerializer(serializers.ModelSerializer):

    total_purchases = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()
    outstanding_balance = serializers.SerializerMethodField()

    class Meta:
        model = Customer

        fields = [
            "id",
            "name",
            "phone",
            "address",
            "total_purchases",
            "total_paid",
            "outstanding_balance",
        ]

        read_only_fields = [
            "id",
            "total_purchases",
            "total_paid",
            "outstanding_balance",
        ]

    def get_total_purchases(self, obj):
        from django.db.models import Sum

        result = obj.sale_set.aggregate(
            total=Sum("total_amount")
        )

        return result["total"] or 0

    def get_total_paid(self, obj):
        from django.db.models import Sum

        from payments.models import Payment

        result = Payment.objects.filter(
            sale__customer=obj,
            status="completed",
        ).aggregate(
            total=Sum("amount")
        )

        return result["total"] or 0

    def get_outstanding_balance(self, obj):

        purchases = self.get_total_purchases(obj)
        paid = self.get_total_paid(obj)

        return purchases - paid


# ============================================================
# SALE ITEM
# ============================================================

class SaleItemSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )

    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = SaleItem

        fields = [
            "id",
            "sale",
            "product",
            "product_name",
            "product_unit",
            "quantity",
            "price",
            "subtotal",
        ]

        read_only_fields = [
            "id",
            "subtotal",
        ]

    def get_subtotal(self, obj):

        return obj.quantity * obj.price


# ============================================================
# SALE
# ============================================================

class SaleSerializer(serializers.ModelSerializer):

    items = SaleItemSerializer(
        many=True
    )

    cashier_name = serializers.CharField(
        source="cashier.username",
        read_only=True,
    )

    customer_name = serializers.CharField(
        source="customer.name",
        read_only=True,
    )

    class Meta:
        model = Sale

        fields = [
            "id",
            "cashier",
            "cashier_name",
            "customer",
            "customer_name",
            "total_amount",
            "created_at",
            "items",
        ]

        read_only_fields = [
            "id",
            "total_amount",
            "created_at",
        ]

    def create(self, validated_data):

        items_data = validated_data.pop(
            "items",
            []
        )

        sale = Sale.objects.create(
            **validated_data
        )

        total = 0

        for item_data in items_data:

            item = SaleItem.objects.create(
                sale=sale,
                **item_data
            )

            total += item.quantity * item.price

        sale.total_amount = total
        sale.save(
            update_fields=["total_amount"]
        )

        return sale


# ============================================================
# LOCATION
# ============================================================

class LocationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Location
        fields = "__all__"

        read_only_fields = [
            "id",
            "created_at",
        ]


# ============================================================
# INVENTORY BALANCE
# ============================================================

class InventoryBalanceSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )

    location_name = serializers.CharField(
        source="location.name",
        read_only=True,
    )

    class Meta:
        model = InventoryBalance

        fields = [
            "id",
            "product",
            "product_name",
            "location",
            "location_name",
            "status",
            "quantity",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "updated_at",
        ]

    def validate_quantity(self, value):

        if value < 0:
            raise serializers.ValidationError(
                "Inventory quantity cannot be negative."
            )

        return value


# ============================================================
# INVENTORY MOVEMENT
# ============================================================

class InventoryMovementSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )

    location_name = serializers.CharField(
        source="location.name",
        read_only=True,
    )

    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = InventoryMovement

        fields = [
            "id",
            "product",
            "product_name",
            "location",
            "location_name",
            "movement_type",
            "quantity",
            "reason",
            "reference",
            "created_by",
            "created_by_name",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_by",
            "created_at",
        ]

    def get_created_by_name(self, obj):

        if obj.created_by:
            return obj.created_by.username

        return None