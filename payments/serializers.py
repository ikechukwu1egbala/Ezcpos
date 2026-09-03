from rest_framework import serializers
from .models import Payment


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
            "created_at",
        ]

        read_only_fields = [
            "id",
            "processed_by",
            "created_at",
        ]

    def validate_amount(self, value):

        if value <= 0:
            raise serializers.ValidationError(
                "Payment amount must be greater than zero."
            )

        return value