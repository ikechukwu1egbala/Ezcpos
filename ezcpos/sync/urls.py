from django.urls import path

from .views import (
    DeviceView,
    SyncPullView,
    SyncPushView,
)


urlpatterns = [
    path(
        "devices/",
        DeviceView.as_view(),
        name="sync-devices",
    ),
    path(
        "push/",
        SyncPushView.as_view(),
        name="sync-push",
    ),
    path(
        "pull/",
        SyncPullView.as_view(),
        name="sync-pull",
    ),
]
