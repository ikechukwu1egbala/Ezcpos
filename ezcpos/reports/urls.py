from django.urls import path

from .views import (
    ReportSummaryView,
    DailySalesReportView,
    PaymentMethodReportView,
    TopProductsReportView,
    ExpenseReportView,
)

urlpatterns = [
    path(
        "summary/",
        ReportSummaryView.as_view(),
        name="report-summary",
    ),
    path(
        "daily-sales/",
        DailySalesReportView.as_view(),
        name="daily-sales-report",
    ),
    path(
        "payment-methods/",
        PaymentMethodReportView.as_view(),
        name="payment-method-report",
    ),
    path(
        "top-products/",
        TopProductsReportView.as_view(),
        name="top-products-report",
    ),
    path(
        "expenses/",
        ExpenseReportView.as_view(),
        name="expense-report",
    ),
]
