from decimal import Decimal

from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.utils.dateparse import parse_date

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from pos.models import Sale, SaleItem
from expenses.models import Expense

from .serializers import (
    ReportSummarySerializer,
    PaymentMethodReportSerializer,
    ProductSalesReportSerializer,
    ExpenseReportSerializer,
)


class ReportBaseView(APIView):
    permission_classes = [IsAuthenticated]

    def get_date_range(self, request):
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        return (
            parse_date(date_from) if date_from else None,
            parse_date(date_to) if date_to else None,
        )

    def filter_sales(self, request):
        queryset = Sale.objects.all()

        date_from, date_to = self.get_date_range(request)

        if date_from:
            queryset = queryset.filter(
                created_at__date__gte=date_from
            )

        if date_to:
            queryset = queryset.filter(
                created_at__date__lte=date_to
            )

        return queryset


class ReportSummaryView(ReportBaseView):

    def get(self, request):
        sales = self.filter_sales(request)

        expenses = Expense.objects.filter(
            status="paid"
        )

        date_from, date_to = self.get_date_range(request)

        if date_from:
            expenses = expenses.filter(
                expense_date__gte=date_from
            )

        if date_to:
            expenses = expenses.filter(
                expense_date__lte=date_to
            )

        total_sales = sales.aggregate(
            total=Coalesce(
                Sum("total_amount"),
                Decimal("0.00"),
            )
        )["total"]

        total_expenses = expenses.aggregate(
            total=Coalesce(
                Sum("amount"),
                Decimal("0.00"),
            )
        )["total"]

        total_items_sold = SaleItem.objects.filter(
            sale__in=sales
        ).aggregate(
            total=Coalesce(
                Sum("quantity"),
                Decimal("0.00"),
            )
        )["total"]

        transaction_count = sales.count()

        net_after_expenses = (
            total_sales - total_expenses
        )

        data = {
            "total_sales": total_sales,
            "total_expenses": total_expenses,
            "net_after_expenses": net_after_expenses,
            "transaction_count": transaction_count,
            "total_items_sold": total_items_sold,
        }

        serializer = ReportSummarySerializer(data)

        return Response(serializer.data)


class DailySalesReportView(ReportBaseView):

    def get(self, request):
        sales = self.filter_sales(request)

        data = list(
            sales
            .values("created_at__date")
            .annotate(
                total_sales=Coalesce(
                    Sum("total_amount"),
                    Decimal("0.00"),
                ),
                transaction_count=Count("id"),
            )
            .order_by("created_at__date")
        )

        return Response(data)


class PaymentMethodReportView(ReportBaseView):

    def get(self, request):
        sales = self.filter_sales(request)

        data = list(
            sales
            .filter(
                payments__status="completed"
            )
            .values(
                "payments__payment_method"
            )
            .annotate(
                total=Coalesce(
                    Sum("payments__amount"),
                    Decimal("0.00"),
                ),
                transaction_count=Count(
                    "payments",
                    distinct=True,
                ),
            )
            .order_by("-total")
        )

        result = []

        for row in data:
            result.append({
                "payment_method": row[
                    "payments__payment_method"
                ],
                "total": row["total"],
                "transaction_count": row[
                    "transaction_count"
                ],
            })

        serializer = PaymentMethodReportSerializer(
            result,
            many=True,
        )

        return Response(serializer.data)


class TopProductsReportView(ReportBaseView):

    def get(self, request):
        sales = self.filter_sales(request)

        items = (
            SaleItem.objects
            .filter(sale__in=sales)
            .values(
                "product_id",
                "product__name",
            )
            .annotate(
                quantity_sold=Coalesce(
                    Sum("quantity"),
                    Decimal("0.00"),
                ),
                sales_total=Coalesce(
                    Sum(
                        ExpressionWrapper(
                            F("quantity") * F("price"),
                            output_field=DecimalField(
                                max_digits=14,
                                decimal_places=2,
                            ),
                        )
                    ),
                    Decimal("0.00"),
                ),
            )
            .order_by("-sales_total")
        )

        limit = request.query_params.get(
            "limit",
            "20",
        )

        try:
            limit = max(1, min(int(limit), 100))
        except (ValueError, TypeError):
            limit = 20

        items = items[:limit]

        result = []

        for row in items:
            result.append({
                "product_id": row["product_id"],
                "product_name": row["product__name"],
                "quantity_sold": row["quantity_sold"],
                "sales_total": row["sales_total"],
            })

        serializer = ProductSalesReportSerializer(
            result,
            many=True,
        )

        return Response(serializer.data)


class ExpenseReportView(ReportBaseView):

    def get(self, request):
        expenses = Expense.objects.filter(
            status="paid"
        )

        date_from, date_to = self.get_date_range(request)

        if date_from:
            expenses = expenses.filter(
                expense_date__gte=date_from
            )

        if date_to:
            expenses = expenses.filter(
                expense_date__lte=date_to
            )

        data = list(
            expenses
            .values(
                "category_id",
                "category__name",
            )
            .annotate(
                total=Coalesce(
                    Sum("amount"),
                    Decimal("0.00"),
                ),
                transaction_count=Count("id"),
            )
            .order_by("-total")
        )

        result = []

        for row in data:
            result.append({
                "category_id": row["category_id"],
                "category_name": row["category__name"],
                "total": row["total"],
                "transaction_count": row[
                    "transaction_count"
                ],
            })

        serializer = ExpenseReportSerializer(
            result,
            many=True,
        )

        return Response(serializer.data)
