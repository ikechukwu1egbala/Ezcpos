from django.urls import path
from .views import DailySalesReport

urlpatterns = [
    path("daily/", DailySalesReport.as_view())
]