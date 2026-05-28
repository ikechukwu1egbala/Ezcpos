from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from pos.views import ProductViewSet, SaleViewSet
from django.http import HttpResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

def home(request):
    return HttpResponse("EZC POS API is running 🚀")


router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'sales', SaleViewSet)

urlpatterns = [
    path("", home),
    path('admin/', admin.site.urls),
    
    # JWT endpoints
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    path("api/users/", include("users.urls")),
    path("api/pos/", include("pos.urls")),
    path("api/inventory/", include("inventory.urls")),
    path("api/reports/", include("reports.urls")),
    #path("api/payments/", include("payments.urls")),
    
]