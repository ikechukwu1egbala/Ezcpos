from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PaymentViewSet,
    RefundViewSet,
    SalesReturnViewSet,
)


router = DefaultRouter()

router.register(
    r"refunds",
    RefundViewSet,
    basename="refund",
)

router.register(
    r"returns",
    SalesReturnViewSet,
    basename="sales-return",
)

router.register(
    r"",
    PaymentViewSet,
    basename="payment",
)


urlpatterns = [
    path(
        "",
        include(router.urls),
    ),
]
