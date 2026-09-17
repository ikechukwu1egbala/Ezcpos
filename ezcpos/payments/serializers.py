from decimal import Decimal

from django.db.models import Sum
from rest_framework import serializers

from .models import Payment, Refund


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
        total = (
            obj.refunds.aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

        return total

    def get_refundable_amount(self, obj):
        total_refunded = self.get_total_refunded(obj)

        refundable = obj.amount - total_refunded

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
