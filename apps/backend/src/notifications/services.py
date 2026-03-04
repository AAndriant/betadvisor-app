import logging
import requests
from django.conf import settings
from notifications.models import PushToken, Notification

logger = logging.getLogger(__name__)


def send_push_notification(user, title, body, data=None, notification_type=None, sender=None):
    """
    Send a push notification to all active devices of a user via Expo Push API.
    Also creates a Notification record for in-app history.
    """
    # 1. Create notification record
    notification = Notification.objects.create(
        recipient=user,
        sender=sender,
        notification_type=notification_type or Notification.NotificationType.NEW_COMMENT,
        title=title,
        body=body,
        data=data,
    )

    # 2. Get all active push tokens for this user
    tokens = PushToken.objects.filter(user=user, is_active=True).values_list('token', flat=True)

    if not tokens:
        logger.info(f"No active push tokens for user {user.username}, skipping push")
        return notification

    # 3. Build messages for Expo Push API
    messages = []
    for token in tokens:
        message = {
            "to": token,
            "sound": "default",
            "title": title,
            "body": body,
        }
        if data:
            message["data"] = data
        messages.append(message)

    # 4. Send via Expo Push API
    try:
        expo_url = getattr(settings, 'EXPO_PUSH_URL', 'https://exp.host/--/api/v2/push/send')
        response = requests.post(
            expo_url,
            json=messages,
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            timeout=10,
        )
        response.raise_for_status()

        result = response.json()
        logger.info(f"Push notification sent to {len(tokens)} device(s) for user {user.username}")

        # Mark invalid tokens as inactive
        if 'data' in result:
            for i, ticket in enumerate(result['data']):
                if ticket.get('status') == 'error':
                    error_type = ticket.get('details', {}).get('error', '')
                    if error_type in ('DeviceNotRegistered', 'InvalidCredentials'):
                        token_value = list(tokens)[i] if i < len(tokens) else None
                        if token_value:
                            PushToken.objects.filter(token=token_value).update(is_active=False)
                            logger.warning(f"Deactivated invalid push token: {token_value[:30]}...")

        notification.push_sent = True
        notification.save()

    except requests.RequestException as e:
        logger.error(f"Failed to send push notification: {e}")

    return notification


def notify_new_follower(follower, followed_user):
    """Notify a user that someone followed them."""
    send_push_notification(
        user=followed_user,
        title="Nouveau follower ! 🎉",
        body=f"{follower.username} vous suit maintenant",
        data={"type": "new_follower", "follower_id": str(follower.id)},
        notification_type=Notification.NotificationType.NEW_FOLLOWER,
        sender=follower,
    )


def notify_new_like(liker, bet):
    """Notify bet author that someone liked their bet."""
    if liker == bet.author:
        return  # Don't notify self-likes
    send_push_notification(
        user=bet.author,
        title="Nouveau like ! ❤️",
        body=f"{liker.username} a aimé votre pronostic sur {bet.match_title}",
        data={"type": "new_like", "bet_id": str(bet.id)},
        notification_type=Notification.NotificationType.NEW_LIKE,
        sender=liker,
    )


def notify_new_comment(commenter, bet):
    """Notify bet author that someone commented on their bet."""
    if commenter == bet.author:
        return  # Don't notify self-comments
    send_push_notification(
        user=bet.author,
        title="Nouveau commentaire ! 💬",
        body=f"{commenter.username} a commenté votre pronostic sur {bet.match_title}",
        data={"type": "new_comment", "bet_id": str(bet.id)},
        notification_type=Notification.NotificationType.NEW_COMMENT,
        sender=commenter,
    )


def notify_prediction_resolved(prediction):
    """Notify tipster that their prediction has been verified."""
    outcome_emoji = {
        'CORRECT': '✅', 'INCORRECT': '❌', 'VOID': '🔄'
    }
    emoji = outcome_emoji.get(prediction.outcome, '📊')
    send_push_notification(
        user=prediction.bet_ticket.author,
        title=f"Prédiction vérifiée {emoji}",
        body=f"{prediction.match_title}: {prediction.prediction_value} — {prediction.get_outcome_display()}",
        data={
            "type": "prediction_resolved",
            "bet_id": str(prediction.bet_ticket_id),
            "outcome": prediction.outcome,
        },
        notification_type=Notification.NotificationType.PREDICTION_RESOLVED,
    )
