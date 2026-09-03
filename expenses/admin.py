from django.contrib import admin

from .models import Expense, ExpenseCategory


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "is_active",
    )

    search_fields = (
        "name",
    )


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):

    list_display = (
        "description",
        "category",
        "amount",
        "payment_method",
        "status",
        "location",
        "expense_date",
        "recorded_by",
    )

    list_filter = (
        "category",
        "payment_method",
        "status",
        "location",
        "expense_date",
    )

    search_fields = (
        "description",
        "reference",
        "receipt_number",
    )

    date_hierarchy = "expense_date"