from rest_framework.permissions import BasePermission


class IsCartItemOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.owner == request.user:
            return True
        return False


class IsSellerOfOrder(BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.seller == request.user:
            return True
        return False
