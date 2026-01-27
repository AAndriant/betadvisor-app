from rest_framework import permissions

class IsTipster(permissions.BasePermission):
    """
    Custom permission to only allow tipsters to perform actions.
    """

    def has_permission(self, request, view):
        # Check if user is authenticated and is a tipster
        return bool(request.user and request.user.is_authenticated and request.user.is_tipster)
