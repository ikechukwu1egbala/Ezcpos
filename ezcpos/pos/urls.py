from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CategoryViewSet, CustomerViewSet, SaleViewSet

router = DefaultRouter()
router.register("products", ProductViewSet)
router.register("categories", CategoryViewSet)
router.register("customers", CustomerViewSet)
router.register("sales", SaleViewSet)

urlpatterns = [
    path("", include(router.urls)),
]