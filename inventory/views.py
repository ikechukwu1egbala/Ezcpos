#from rest_framework.viewsets import ModelViewSet
#from .models import Product
#from .serializers import ProductSerializer
#from rest_framework.permissions import IsAuthenticated


#class ProductViewSet(ModelViewSet):
#    queryset = Product.objects.all()
#    serializer_class = ProductSerializer
#    permission_classes = [IsAuthenticated]

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import InventoryLog
from .serializers import InventorySerializer


class InventoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InventoryLog.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]