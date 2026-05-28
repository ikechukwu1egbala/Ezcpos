from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import Product, Sale, Category, Customer 
from .serializers import (
    ProductSerializer,
    CategorySerializer,
    CustomerSerializer,
    SaleSerializer
)
from .services import create_sale


from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "admin"

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]



#class ProductViewSet(viewsets.ModelViewSet):
#    queryset = Product.objects.all()
#    serializer_class = ProductSerializer


class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer

    def create(self, request, *args, **kwargs):
        product_id = request.data.get("product")
        quantity = int(request.data.get("quantity"))

        sale = create_sale(product_id, quantity, request.user)

        serializer = self.get_serializer(sale)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



#class ProductViewSet(viewsets.ModelViewSet):
#    queryset = Product.objects.all()
#    serializer_class = ProductSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer