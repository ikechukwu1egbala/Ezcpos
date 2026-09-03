from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Expense, ExpenseCategory
from .serializers import (
    ExpenseSerializer,
    ExpenseCategorySerializer,
)


class ExpenseCategoryViewSet(viewsets.ModelViewSet):

    queryset = ExpenseCategory.objects.all()
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

    def perform_create(self, serializer):

        serializer.save(
            recorded_by=self.request.user
        )