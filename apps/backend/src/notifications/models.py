from django.db import models
from django.conf import settings
from core.models import TimeStampedModel


class PushToken(TimeStampedModel):
    """
    Stores Expo push notification tokens for users.
    A user can have multiple tokens (multiple devices).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='push_tokens'
    )
    token = models.CharField(
        max_length=255,
        unique=True,
        help_text='Expo push token (ExponentPushToken[...])'
    )
    device_name = models.CharField(max_length=128, blank=True, default='')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f"{self.user.username} — {self.token[:30]}..."


class Notification(TimeStampedModel):
    """
    Stores notification history for audit and in-app notification center.
    """
    class NotificationType(models.TextChoices):
        NEW_FOLLOWER = 'NEW_FOLLOWER', 'New Follower'
        NEW_LIKE = 'NEW_LIKE', 'New Like'
        NEW_COMMENT = 'NEW_COMMENT', 'New Comment'
        PREDICTION_RESOLVED = 'PREDICTION_RESOLVED', 'Prediction Resolved'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications'
    )
    notification_type = models.CharField(
        max_length=25,
        choices=NotificationType.choices
    )
    title = models.CharField(max_length=255)
    body = models.TextField(max_length=500)
    data = models.JSONField(null=True, blank=True, help_text='Extra payload data')
    is_read = models.BooleanField(default=False)
    push_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f"[{self.notification_type}] → {self.recipient.username}: {self.title}"
