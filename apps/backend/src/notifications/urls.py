from django.urls import path
from .views import RegisterPushTokenView, NotificationListView, MarkNotificationsReadView

urlpatterns = [
    path('push-token/', RegisterPushTokenView.as_view(), name='register-push-token'),
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/read/', MarkNotificationsReadView.as_view(), name='mark-notifications-read'),
]
