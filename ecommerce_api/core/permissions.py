from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrStaff(BasePermission):
    """
    Custom permission to allow only owners or staff to update/delete products.
    """

    def has_object_permission(self, request, view, obj):
        # Allow safe methods (GET, HEAD, OPTIONS) for everyone
        if request.method in SAFE_METHODS:
            return True
        # Allow staff users to update/delete any product
        if request.user.is_staff:
            return True
        # Allow owners to update/delete their own products
        return obj.user == request.user
