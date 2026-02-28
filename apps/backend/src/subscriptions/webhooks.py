import logging
import stripe
from datetime import datetime, timezone
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from subscriptions.models import Subscription, StripeEvent
from users.models import CustomUser
from connect.models import ConnectedAccount

logger = logging.getLogger(__name__)


class StripeWebhookPayloadError(Exception):
    """Raised when the payload is invalid."""
    pass


class StripeWebhookSignatureError(Exception):
    """Raised when the webhook signature verification fails."""
    pass


def process_stripe_webhook_payload(payload, sig_header, webhook_secret):
    """
    Validates the Stripe webhook signature and routes the event to the correct handler.
    """
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        raise StripeWebhookPayloadError("Invalid payload") from e
    except stripe.error.SignatureVerificationError as e:
        raise StripeWebhookSignatureError("Invalid signature") from e

    _handle_stripe_event(event)


def _handle_stripe_event(event):
    event_id = event['id']
    event_type = event['type']

    logger.info(f"Received webhook event {event_id} of type {event_type}")

    handler = HANDLERS.get(event_type)
    if not handler:
        logger.info(f"Unhandled event type: {event_type}")
        return

    # Idempotency check with row-level lock
    with transaction.atomic():
        stripe_event, created = StripeEvent.objects.select_for_update().get_or_create(
            stripe_event_id=event_id,
            defaults={
                'event_type': event_type,
                'payload': event
            }
        )

        if not created:
            logger.info(f"Event {event_id} already processed, skipping.")
            return

        handler(event)


def _handle_checkout_session_completed(event):
    session = event['data']['object']
    if session.get('mode') != 'subscription':
        return

    metadata = session.get('metadata', {})
    follower_id = metadata.get('follower_id')
    tipster_id = metadata.get('tipster_id')

    if not follower_id or not tipster_id:
        logger.error(f"checkout.session.completed missing follower_id or tipster_id in metadata: {session['id']}")
        return

    stripe_subscription_id = session.get('subscription')
    stripe_customer_id = session.get('customer')

    try:
        follower = CustomUser.objects.get(id=follower_id)
        tipster = CustomUser.objects.get(id=tipster_id)
    except CustomUser.DoesNotExist:
        logger.error(f"CustomUser not found for follower_id {follower_id} or tipster_id {tipster_id}")
        return

    subscription, created = Subscription.objects.update_or_create(
        follower=follower,
        tipster=tipster,
        defaults={
            'stripe_subscription_id': stripe_subscription_id,
            'stripe_customer_id': stripe_customer_id,
            'status': 'active'
        }
    )
    logger.info(f"checkout.session.completed: updated/created subscription {subscription.id}")


def _handle_invoice_paid(event):
    invoice = event['data']['object']
    stripe_subscription_id = invoice.get('subscription')

    if not stripe_subscription_id:
        return

    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription_id)
    except Subscription.DoesNotExist:
        logger.error(f"invoice.paid: Subscription not found for stripe_subscription_id {stripe_subscription_id}")
        return

    # Update current_period_end based on invoice lines
    # The invoice usually contains the subscription period in its lines
    lines = invoice.get('lines', {}).get('data', [])
    current_period_end = None
    for line in lines:
        if line.get('type') == 'subscription':
            period = line.get('period', {})
            end_timestamp = period.get('end')
            if end_timestamp:
                current_period_end = datetime.fromtimestamp(end_timestamp, tz=timezone.utc)
                break

    # Alternatively we could retrieve the subscription from Stripe to get current_period_end reliably
    # But usually it's in the invoice line item.
    if current_period_end:
        subscription.current_period_end = current_period_end

    subscription.status = 'active'
    subscription.save()
    logger.info(f"invoice.paid: updated subscription {subscription.id} status to active")


def _handle_invoice_payment_failed(event):
    invoice = event['data']['object']
    stripe_subscription_id = invoice.get('subscription')

    if not stripe_subscription_id:
        return

    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription_id)
    except Subscription.DoesNotExist:
        logger.error(f"invoice.payment_failed: Subscription not found for stripe_subscription_id {stripe_subscription_id}")
        return

    subscription.status = 'past_due'
    subscription.save()
    logger.info(f"invoice.payment_failed: updated subscription {subscription.id} status to past_due")


def _handle_customer_subscription_deleted(event):
    stripe_subscription = event['data']['object']
    stripe_subscription_id = stripe_subscription.get('id')

    if not stripe_subscription_id:
        return

    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription_id)
    except Subscription.DoesNotExist:
        logger.error(f"customer.subscription.deleted: Subscription not found for stripe_subscription_id {stripe_subscription_id}")
        return

    subscription.status = 'canceled'
    subscription.save()
    logger.info(f"customer.subscription.deleted: updated subscription {subscription.id} status to canceled")


def _handle_account_updated(event):
    account = event['data']['object']
    stripe_account_id = account.get('id')
    charges_enabled = account.get('charges_enabled', False)
    payouts_enabled = account.get('payouts_enabled', False)

    if not stripe_account_id:
        return

    try:
        connected_account = ConnectedAccount.objects.get(stripe_account_id=stripe_account_id)
    except ConnectedAccount.DoesNotExist:
        logger.error(f"account.updated: ConnectedAccount not found for stripe_account_id {stripe_account_id}")
        return

    connected_account.charges_enabled = charges_enabled
    connected_account.payouts_enabled = payouts_enabled

    if charges_enabled and payouts_enabled:
        connected_account.onboarding_completed = True

    connected_account.save()
    logger.info(f"account.updated: updated connected_account {connected_account.id} (charges: {charges_enabled}, payouts: {payouts_enabled}, onboarding: {connected_account.onboarding_completed})")


HANDLERS = {
    'checkout.session.completed': _handle_checkout_session_completed,
    'invoice.paid': _handle_invoice_paid,
    'invoice.payment_failed': _handle_invoice_payment_failed,
    'customer.subscription.deleted': _handle_customer_subscription_deleted,
    'account.updated': _handle_account_updated,
}
