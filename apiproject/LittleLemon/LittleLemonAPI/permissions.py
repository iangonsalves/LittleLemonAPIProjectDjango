from rest_framework import permissions


class IsManager(permissions.BasePermission):
    """
    Check if user is in Manager group and is Authenticated
    """
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.groups.filter(name='Manager'))
