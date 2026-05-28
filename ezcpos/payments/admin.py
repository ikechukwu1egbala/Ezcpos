from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("sale", "amount", "payment_method", "status", "created_at")
    list_filter = ("payment_method", "status")
    search_fields = ("transaction_reference",)