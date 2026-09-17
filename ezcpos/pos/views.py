from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Product,
    Category,
    Customer,
    Sale,
    SaleItem,
    Location,
    InventoryBalance,
    InventoryMovement,
)
from .serializers import (
    ProductSerializer,
    CategorySerializer,
    CustomerSerializer,
    SaleSerializer,
    SaleItemSerializer,
    LocationSerializer,
    InventoryBalanceSerializer,
    InventoryMovementSerializer,
)
from .services import create_sale


class ProductViewSet(viewsets.ModelViewSet):
    """
    Products API.

    All product operations require authentication.
    """

    queryset = Product.objects.all().order_by("-created_at")
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


class CategoryViewSet(viewsets.ModelViewSet):
    """
    Categories API.
    """

    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class CustomerViewSet(viewsets.ModelViewSet):
    """
    Customers API.
    """

    queryset = Customer.objects.all().order_by("name")
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]


class SaleViewSet(viewsets.ModelViewSet):
    """
    Sales API.

    Sales are created through the service layer so that:

    1. The sale is created.
    2. Sale items are created.
    3. Inventory is reduced.
    4. Inventory movements are recorded.

    All of this happens inside one database transaction.
    """

    queryset = (
        Sale.objects
        .select_related("cashier", "customer")
        .prefetch_related("items", "payments")
        .order_by("-created_at")
    )
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        Create a new sale.

        Expected request example:

        {
            "customer": 1,
            "location": 1,
            "items": [
                {
                    "product_id": 1,
                    "quantity": 2
                },
                {
                    "product_id": 3,
                    "quantity": 1,
                    "product_unit_id": 5
                }
            ]
        }
        """

        items = request.data.get("items", [])
        customer_id = request.data.get("customer")
        location_id = request.data.get("location")

        if not items:
            return Response(
                {"detail": "A sale must contain at least one item."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------------------
        # Customer
        # ---------------------------------------------------------
        customer = None

        if customer_id:
            try:
                customer = Customer.objects.get(id=customer_id)
            except Customer.DoesNotExist:
                return Response(
                    {"detail": "Customer not found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # ---------------------------------------------------------
        # Location
        # ---------------------------------------------------------
        location = None

        if location_id:
            try:
                location = Location.objects.get(
                    id=location_id,
                    is_active=True,
                )
            except Location.DoesNotExist:
                return Response(
                    {"detail": "Active inventory location not found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # ---------------------------------------------------------
        # Create sale through service layer
        # ---------------------------------------------------------
        try:
            sale = create_sale(
                items=items,
                cashier=request.user,
                customer=customer,
                location=location,
            )

        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(sale)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


class SaleItemViewSet(viewsets.ModelViewSet):
    """
    Sale items API.

    Normally sale items should be created through a Sale.
    This endpoint is retained for API compatibility.
    """

    queryset = SaleItem.objects.all().select_related(
        "sale",
        "product",
        "product_unit",
    )
    serializer_class = SaleItemSerializer
    permission_classes = [IsAuthenticated]


class LocationViewSet(viewsets.ModelViewSet):
    """
    Store/warehouse locations API.
    """

    queryset = Location.objects.all().order_by("name")
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]


class InventoryBalanceViewSet(viewsets.ModelViewSet):
    """
    Current inventory balances API.
    """

    queryset = (
        InventoryBalance.objects
        .select_related("product", "location")
        .order_by("product__name", "location__name")
    )
    serializer_class = InventoryBalanceSerializer
    permission_classes = [IsAuthenticated]


class InventoryMovementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Inventory history API.

    Inventory movements are created by the system rather than
    manually through this endpoint.
    """

    queryset = (
        InventoryMovement.objects
        .select_related("product", "location", "created_by")
        .order_by("-created_at")
    )
    serializer_class = InventoryMovementSerializer
    permission_classes = [IsAuthenticated]
