from django.shortcuts import get_object_or_404

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status

from .models import Payment, Refund
from .serializers import PaymentSerializer, RefundSerializer
from .services import process_payment, refund_payment
from pos.models import Sale


class PaymentViewSet(ModelViewSet):

    queryset = Payment.objects.select_related(
        "sale",
        "processed_by",
    ).prefetch_related(
        "refunds",
    ).all()

    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):

        sale_id = request.data.get("sale")
        amount = request.data.get("amount")
        method = request.data.get("payment_method")
        reference = request.data.get(
            "transaction_reference"
        )

        if not sale_id:
            return Response(
                {"detail": "Sale is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if amount is None:
            return Response(
                {"detail": "Payment amount is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not method:
            return Response(
                {"detail": "Payment method is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sale = get_object_or_404(
            Sale,
            pk=sale_id,
        )

        try:
            payment = process_payment(
                sale=sale,
                amount=amount,
                method=method,
                user=request.user,
                reference=reference,
            )

        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(payment)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["post"],
    )
    def refund(self, request, pk=None):

        payment = self.get_object()

        amount = request.data.get("amount")
        reason = request.data.get("reason")
        reference = request.data.get("reference")

        if amount is None:
            return Response(
                {"detail": "Refund amount is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not reason:
            return Response(
                {"detail": "Refund reason is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            refund = refund_payment(
                payment=payment,
                amount=amount,
                reason=reason,
                user=request.user,
                reference=reference,
            )

        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RefundSerializer(refund)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


class RefundViewSet(ModelViewSet):

    queryset = Refund.objects.select_related(
        "payment",
        "payment__sale",
        "processed_by",
    ).all()

    serializer_class = RefundSerializer
    permission_classes = [IsAuthenticated]

    http_method_names = [
        "get",
        "head",
        "options",
    ]
