from rest_framework import serializers

from .models import Device, SyncOperation


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = (
            "id",
            "name",
            "device_identifier",
            "user",
            "is_active",
            "last_sync_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "user",
            "last_sync_at",
            "created_at",
            "updated_at",
        )


class SyncOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncOperation
        fields = (
            "operation_id",
            "device",
            "entity_type",
            "entity_id",
            "operation_type",
            "payload",
        )
        read_only_fields = ("device",)


class SyncPushSerializer(serializers.Serializer):
    device_id = serializers.UUIDField()
    operations = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False,
    )


class SyncPullSerializer(serializers.Serializer):
    device_id = serializers.UUIDField()
    since = serializers.DateTimeField(
        required=False,
        allow_null=True,
    )
