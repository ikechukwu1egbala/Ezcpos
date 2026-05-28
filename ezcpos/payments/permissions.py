from rest_framework.permissions import BasePermission


class IsCashierOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ["admin", "manager", "cashier"]