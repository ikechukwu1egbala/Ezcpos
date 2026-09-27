from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Device, SyncOperation
from .serializers import (
    DeviceSerializer,
    SyncPullSerializer,
    SyncPushSerializer,
)
from .services import SyncService


class DeviceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        devices = (
            Device.objects
            .filter(user=request.user)
            .order_by("-created_at")
        )

        serializer = DeviceSerializer(
            devices,
            many=True,
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = DeviceSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        device = serializer.save(
            user=request.user,
        )

        return Response(
            DeviceSerializer(device).data,
            status=status.HTTP_201_CREATED,
        )


class SyncPushView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SyncPushSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        device_id = serializer.validated_data["device_id"]
        operations = serializer.validated_data["operations"]

        device = (
            Device.objects
            .filter(
                id=device_id,
                user=request.user,
                is_active=True,
            )
            .first()
        )

        if device is None:
            return Response(
                {
                    "detail": (
                        "Device not found or inactive."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        results = []

        for operation in operations:
            try:
                result = SyncService.receive_operation(
                    device=device,
                    user=request.user,
                    operation=operation,
                )

            except Exception as exc:
                result = {
                    "operation_id": operation.get(
                        "operation_id"
                    ),
                    "status": "failed",
                    "duplicate": False,
                    "server_result": {},
                    "error_message": str(exc),
                }

            results.append(result)

        device.last_sync_at = timezone.now()

        device.save(
            update_fields=["last_sync_at"]
        )

        return Response(
            {
                "device_id": str(device.id),
                "processed_at": timezone.now(),
                "results": results,
            }
        )


class SyncPullView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SyncPullSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        device_id = serializer.validated_data["device_id"]
        since = serializer.validated_data.get("since")

        device = (
            Device.objects
            .filter(
                id=device_id,
                user=request.user,
                is_active=True,
            )
            .first()
        )

        if device is None:
            return Response(
                {
                    "detail": (
                        "Device not found or inactive."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        operations = SyncOperation.objects.filter(
            status="processed",
        )

        if since:
            operations = operations.filter(
                processed_at__gt=since,
            )

        operations = operations.order_by(
            "processed_at",
            "created_at",
        )

        data = []

        for operation in operations:
            data.append(
                {
                    "operation_id": str(
                        operation.operation_id
                    ),
                    "entity_type": operation.entity_type,
                    "entity_id": operation.entity_id,
                    "operation_type": operation.operation_type,
                    "payload": operation.payload,
                    "server_result": operation.server_result,
                    "processed_at": operation.processed_at,
                }
            )

        return Response(
            {
                "device_id": str(device.id),
                "server_time": timezone.now(),
                "operations": data,
            }
        )
