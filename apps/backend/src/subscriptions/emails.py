from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_new_subscriber_email(tipster, follower):
    """Notify tipster of a new subscriber."""
    try:
        send_mail(
            subject=f"New subscriber: {follower.username}",
            message=f"Congratulations! {follower.username} just subscribed to your tips.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[tipster.email],
            fail_silently=True,
        )
    except Exception as e:
        logger.error(f"Failed to send new subscriber email: {e}")

def send_subscription_canceled_email(tipster, follower):
    """Notify tipster that a subscriber canceled."""
    try:
        send_mail(
            subject=f"Subscriber lost: {follower.username}",
            message=f"{follower.username} has canceled their subscription.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[tipster.email],
            fail_silently=True,
        )
    except Exception as e:
        logger.error(f"Failed to send cancelation email: {e}")

def send_welcome_subscriber_email(follower, tipster):
    """Welcome email to new subscriber."""
    try:
        send_mail(
            subject=f"Welcome! You are now subscribed to {tipster.username}",
            message=f"You now have access to {tipster.username}'s premium betting tips.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[follower.email],
            fail_silently=True,
        )
    except Exception as e:
        logger.error(f"Failed to send welcome email: {e}")
