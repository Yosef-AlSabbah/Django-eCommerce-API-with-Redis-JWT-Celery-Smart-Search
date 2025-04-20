from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrAdmin(BasePermission):
    """
    Custom permission that allows access only to the owner of the profile or an admin.
    """

    def has_permission(self, request, view):
        # Allow access if the user is authenticated
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Allow read access, or write access only if user is owner or admin
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user or request.user.is_staff


class IsNotAuthenticated(BasePermission):
    """
    Custom permission that allows access only to non-authenticated users.
    """

    def has_permission(self, request, view):
        return not request.user or not request.user.is_authenticated
