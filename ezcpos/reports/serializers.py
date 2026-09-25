from rest_framework import serializers


class ReportSummarySerializer(serializers.Serializer):
    total_sales = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )
    total_expenses = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )
    net_after_expenses = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )
    transaction_count = serializers.IntegerField()
    total_items_sold = serializers.DecimalField(
        max_digits=18,
        decimal_places=6,
    )


class PaymentMethodReportSerializer(serializers.Serializer):
    payment_method = serializers.CharField()
    total = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )
    transaction_count = serializers.IntegerField()


class ProductSalesReportSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    quantity_sold = serializers.DecimalField(
        max_digits=18,
        decimal_places=6,
    )
    sales_total = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )


class ExpenseReportSerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    category_name = serializers.CharField()
    total = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )
    transaction_count = serializers.IntegerField()
