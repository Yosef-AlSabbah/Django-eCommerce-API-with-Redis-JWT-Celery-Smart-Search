from rest_framework import permissions


class IsAdminOrOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        return obj.user == request.user

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
