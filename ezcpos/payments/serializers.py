from decimal import Decimal

from django.db.models import Sum
from rest_framework import serializers

from .models import (
    Payment,
    Refund,
    SalesReturn,
    SalesReturnItem,
)


class PaymentSerializer(serializers.ModelSerializer):
    processed_by_name = serializers.CharField(
        source="processed_by.username",
        read_only=True,
    )

    sale_total = serializers.DecimalField(
        source="sale.total_amount",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    total_refunded = serializers.SerializerMethodField()
    refundable_amount = serializers.SerializerMethodField()

    class Meta:
        model = Payment

        fields = [
            "id",
            "sale",
            "sale_total",
            "amount",
            "payment_method",
            "transaction_reference",
            "status",
            "processed_by",
            "processed_by_name",
            "total_refunded",
            "refundable_amount",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "processed_by",
            "total_refunded",
            "refundable_amount",
            "created_at",
        ]

    def validate_amount(self, value):
        if value <= Decimal("0.00"):
            raise serializers.ValidationError(
                "Payment amount must be greater than zero."
            )

        return value

    def get_total_refunded(self, obj):
        return (
            obj.refunds.aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

    def get_refundable_amount(self, obj):
        refundable = (
            obj.amount - self.get_total_refunded(obj)
        )

        if refundable < Decimal("0.00"):
            refundable = Decimal("0.00")

        return refundable


class RefundSerializer(serializers.ModelSerializer):
    payment_method = serializers.CharField(
        source="payment.payment_method",
        read_only=True,
    )

    sale = serializers.IntegerField(
        source="payment.sale_id",
        read_only=True,
    )

    processed_by_name = serializers.CharField(
        source="processed_by.username",
        read_only=True,
    )

    class Meta:
        model = Refund

        fields = [
            "id",
            "payment",
            "sale",
            "payment_method",
            "amount",
            "reason",
            "reference",
            "processed_by",
            "processed_by_name",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "processed_by",
            "created_at",
        ]

    def validate_amount(self, value):
        if value <= Decimal("0.00"):
            raise serializers.ValidationError(
                "Refund amount must be greater than zero."
            )

        return value


class SalesReturnItemSerializer(serializers.ModelSerializer):
    product = serializers.IntegerField(
        source="sale_item.product_id",
        read_only=True,
    )

    product_name = serializers.CharField(
        source="sale_item.product.name",
        read_only=True,
    )

    original_quantity = serializers.DecimalField(
        source="sale_item.quantity",
        max_digits=18,
        decimal_places=6,
        read_only=True,
    )

    class Meta:
        model = SalesReturnItem

        fields = [
            "id",
            "sale_item",
            "product",
            "product_name",
            "original_quantity",
            "quantity",
            "refund_amount",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "product",
            "product_name",
            "original_quantity",
            "created_at",
        ]

    def validate_quantity(self, value):
        if value <= Decimal("0"):
            raise serializers.ValidationError(
                "Return quantity must be greater than zero."
            )

        return value


class SalesReturnSerializer(serializers.ModelSerializer):
    processed_by_name = serializers.CharField(
        source="processed_by.username",
        read_only=True,
    )

    items = SalesReturnItemSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = SalesReturn

        fields = [
            "id",
            "sale",
            "refund",
            "location",
            "reason",
            "reference",
            "processed_by",
            "processed_by_name",
            "created_at",
            "items",
        ]

        read_only_fields = [
            "id",
            "processed_by",
            "created_at",
            "items",
        ]
