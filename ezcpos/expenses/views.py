from decimal import Decimal

from django.db.models import Sum, Count
from django.utils.dateparse import parse_date

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Expense, ExpenseCategory
from .serializers import (
    ExpenseSerializer,
    ExpenseCategorySerializer,
)


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    queryset = ExpenseCategory.objects.all().order_by("name")
    serializer_class = ExpenseCategorySerializer
    permission_classes = [IsAuthenticated]


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.select_related(
        "category",
        "location",
        "recorded_by",
    ).all()

    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        category = self.request.query_params.get("category")
        location = self.request.query_params.get("location")
        payment_method = self.request.query_params.get("payment_method")
        status = self.request.query_params.get("status")
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")

        if category:
            queryset = queryset.filter(category_id=category)

        if location:
            queryset = queryset.filter(location_id=location)

        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        if status:
            queryset = queryset.filter(status=status)

        if date_from:
            parsed_date = parse_date(date_from)
            if parsed_date:
                queryset = queryset.filter(expense_date__gte=parsed_date)

        if date_to:
            parsed_date = parse_date(date_to)
            if parsed_date:
                queryset = queryset.filter(expense_date__lte=parsed_date)

        return queryset

    def perform_create(self, serializer):
        serializer.save(
            recorded_by=self.request.user
        )

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        Expense summary for the currently filtered queryset.
        """

        queryset = self.get_queryset()

        total = queryset.filter(
            status="paid"
        ).aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0.00")

        pending = queryset.filter(
            status="pending"
        ).aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0.00")

        cancelled = queryset.filter(
            status="cancelled"
        ).aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0.00")

        count = queryset.count()

        payment_breakdown = list(
            queryset.filter(status="paid")
            .values("payment_method")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("-total")
        )

        category_breakdown = list(
            queryset.filter(status="paid")
            .values(
                "category_id",
                "category__name",
            )
            .annotate(
                total=Sum("amount"),
                count=Count("id"),
            )
            .order_by("-total")
        )

        return Response({
            "total_paid": total,
            "total_pending": pending,
            "total_cancelled": cancelled,
            "expense_count": count,
            "payment_method_breakdown": payment_breakdown,
            "category_breakdown": category_breakdown,
        })
