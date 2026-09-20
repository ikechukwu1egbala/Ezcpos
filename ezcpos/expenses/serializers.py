from rest_framework import serializers

from .models import Expense, ExpenseCategory


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = "__all__"
        read_only_fields = [
            "id",
        ]

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Category name cannot be empty."
            )

        return value


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    location_name = serializers.CharField(
        source="location.name",
        read_only=True,
    )

    recorded_by_name = serializers.CharField(
        source="recorded_by.username",
        read_only=True,
    )

    class Meta:
        model = Expense

        fields = [
            "id",
            "category",
            "category_name",
            "location",
            "location_name",
            "description",
            "amount",
            "payment_method",
            "status",
            "reference",
            "receipt_number",
            "expense_date",
            "recorded_by",
            "recorded_by_name",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "recorded_by",
            "created_at",
            "updated_at",
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Expense amount must be greater than zero."
            )

        return value

    def validate_description(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Expense description cannot be empty."
            )

        return value
