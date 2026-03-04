"""
Django signals to trigger push notifications on social events.
Connected in NotificationsConfig.ready().
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='social.Follow')
def on_new_follow(sender, instance, created, **kwargs):
    """Send push notification when a user follows another."""
    if created:
        try:
            from notifications.services import notify_new_follower
            notify_new_follower(
                follower=instance.follower,
                followed_user=instance.followed,
            )
        except Exception as e:
            logger.error(f"Failed to send follow notification: {e}")


@receiver(post_save, sender='social.Like')
def on_new_like(sender, instance, created, **kwargs):
    """Send push notification when a user likes a bet."""
    if created:
        try:
            from notifications.services import notify_new_like
            notify_new_like(liker=instance.user, bet=instance.bet)
        except Exception as e:
            logger.error(f"Failed to send like notification: {e}")


@receiver(post_save, sender='social.Comment')
def on_new_comment(sender, instance, created, **kwargs):
    """Send push notification when a user comments on a bet."""
    if created:
        try:
            from notifications.services import notify_new_comment
            notify_new_comment(commenter=instance.user, bet=instance.bet)
        except Exception as e:
            logger.error(f"Failed to send comment notification: {e}")
