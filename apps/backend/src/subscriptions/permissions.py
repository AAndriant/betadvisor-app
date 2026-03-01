from rest_framework.permissions import BasePermission
from subscriptions.models import Subscription

class HasActiveSubscription(BasePermission):
    """
    Allows access only to users who have an active subscription.
    """
    message = "You must have an active subscription to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            Subscription.objects.filter(follower=request.user, status='active').exists()
        )
