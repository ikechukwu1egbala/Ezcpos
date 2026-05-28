from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Payment
from .serializers import PaymentSerializer
from .services import process_payment
from pos.models import Sale


class PaymentViewSet(ModelViewSet):

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):

        sale_id = request.data.get("sale")
        amount = request.data.get("amount")
        method = request.data.get("payment_method")
        reference = request.data.get("transaction_reference")

        sale = Sale.objects.get(id=sale_id)

        payment = process_payment(
            sale=sale,
            amount=amount,
            method=method,
            user=request.user,
            reference=reference,
        )

        serializer = self.get_serializer(payment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def refund(self, request, pk=None):
        payment = self.get_object()
        refunded = refund_payment(payment, request.user)
        serializer = self.get_serializer(refunded)
        return Response(serializer.data)
        