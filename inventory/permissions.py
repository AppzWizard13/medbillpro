# permissions.py
from rest_framework.permissions import BasePermission

class IsInventoryManager(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.groups.filter(name='Inventory Manager').exists()
        )