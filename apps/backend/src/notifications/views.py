from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.pagination import CursorPagination
from .models import PushToken, Notification
from .serializers import PushTokenSerializer, NotificationSerializer


class NotificationCursorPagination(CursorPagination):
    """Cursor-based pagination for notifications — efficient for real-time feeds."""
    page_size = 20
    ordering = '-created_at'
    cursor_query_param = 'cursor'


class RegisterPushTokenView(generics.CreateAPIView):
    """
    POST /api/me/push-token/
    Register an Expo push notification token for the authenticated user.
    Upserts: if the token already exists, updates it.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PushTokenSerializer

    def perform_create(self, serializer):
        serializer.save()


class NotificationListView(generics.ListAPIView):
    """
    GET /api/me/notifications/
    List notifications for the authenticated user (cursor-paginated).
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer
    pagination_class = NotificationCursorPagination

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        ).select_related('sender')


class MarkNotificationsReadView(generics.GenericAPIView):
    """
    POST /api/me/notifications/read/
    Mark all notifications as read for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(is_read=True)
        return Response({'marked_read': count})
