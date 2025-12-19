import stripe
import logging
from django.conf import settings
from django.db import transaction, IntegrityError
from django.utils import timezone
from .models import Subscription, Plan, StripeProfile, StripeEvent
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()

# Ensure Stripe API key is set for webhooks
stripe.api_key = settings.STRIPE_SECRET_KEY

def handle_stripe_webhook(payload, sig_header):
    """
    Handles Stripe webhooks securely and atomically.
    """
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        logger.error(f"Invalid payload: {e}")
        raise
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Invalid signature: {e}")
        raise

    # Idempotency check
    event_id = event['id']
    if StripeEvent.objects.filter(event_id=event_id).exists():
        logger.info(f"Event {event_id} already processed.")
        return

    # Handle the event
    event_type = event['type']
    data = event['data']['object']

    try:
        with transaction.atomic():
            # Create StripeEvent record to lock it (handling race conditions)
            try:
                StripeEvent.objects.create(event_id=event_id, type=event_type)
            except IntegrityError:
                logger.info(f"Event {event_id} already processed (race condition caught).")
                return

            if event_type == 'checkout.session.completed':
                _handle_checkout_session_completed(data)
            elif event_type == 'invoice.payment_succeeded':
                _handle_invoice_payment_succeeded(data)
            elif event_type == 'customer.subscription.deleted':
                _handle_subscription_deleted(data)
            elif event_type == 'invoice.payment_failed':
                _handle_payment_failed(data)
            elif event_type == 'account.updated':
                _handle_account_updated(data)
            else:
                logger.info(f"Unhandled event type: {event_type}")
    except Exception as e:
        logger.error(f"Error handling event {event_type}: {e}")
        # Re-raise to let Stripe know it failed (so they retry)
        raise

@transaction.atomic
def _handle_account_updated(account):
    """
    Handles updates to connected accounts, specifically checking charges_enabled.
    """
    stripe_account_id = account.get('id')
    charges_enabled = account.get('charges_enabled', False)

    try:
        profile = StripeProfile.objects.get(stripe_account_id=stripe_account_id)
        if profile.charges_enabled != charges_enabled:
            profile.charges_enabled = charges_enabled
            profile.save()
            logger.info(f"Updated charges_enabled to {charges_enabled} for account {stripe_account_id}")
    except StripeProfile.DoesNotExist:
        logger.warning(f"StripeProfile not found for account {stripe_account_id}")

@transaction.atomic
def _handle_checkout_session_completed(session):
    """
    Handles initial subscription creation.
    """
    if session.get('mode') != 'subscription':
        return

    client_reference_id = session.get('client_reference_id') # If we used it
    metadata = session.get('subscription_data', {}).get('metadata', {})

    # Fallback to verify if metadata is in the session directly or nested in subscription object
    # But in create_checkout_session we put it in subscription_data.metadata
    # Note: Stripe structure can be tricky.
    # In 'checkout.session.completed', the subscription ID is in session['subscription']

    stripe_subscription_id = session['subscription']

    # Fetch the subscription object from Stripe to get metadata if not present in session properly
    stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
    metadata = stripe_sub.metadata

    user_id = metadata.get('user_id')
    plan_id = metadata.get('plan_id')
    platform_fee_percent = metadata.get('platform_fee_percent')

    if not user_id or not plan_id:
        logger.error("Missing user_id or plan_id in subscription metadata")
        return

    try:
        user = User.objects.get(id=user_id)
        plan = Plan.objects.get(id=plan_id)
    except (User.DoesNotExist, Plan.DoesNotExist):
        logger.error("User or Plan not found")
        return

    # Create Subscription record
    Subscription.objects.create(
        subscriber=user,
        plan=plan,
        stripe_subscription_id=stripe_subscription_id,
        status=Subscription.Status.ACTIVE, # Assuming active upon successful payment
        current_period_end=timezone.datetime.fromtimestamp(stripe_sub.current_period_end, tz=timezone.get_fixed_timezone(0)),
        platform_fee_percent=platform_fee_percent or settings.PLATFORM_FEE_PERCENT
    )

@transaction.atomic
def _handle_invoice_payment_succeeded(invoice):
    """
    Handles subscription renewal.
    """
    if invoice.get('billing_reason') == 'subscription_create':
        # Handled by checkout.session.completed usually, but good to ensure date update
        pass

    stripe_subscription_id = invoice.get('subscription')
    if not stripe_subscription_id:
        return

    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription_id)
        # Update current_period_end
        # The invoice object has lines.period.end, but it's safer to check the subscription object or use invoice.period_end (if it represents the sub period)
        # Actually invoice.lines.data[0].period.end is reliable for simple subs

        # Better: fetch subscription from Stripe to be sure, or rely on invoice.lines
        # For efficiency, let's use invoice data if possible, but fetching sub is safer for accurate 'current_period_end'

        # Using the invoice period end usually matches the paid period
        subscription.current_period_end = timezone.datetime.fromtimestamp(invoice['lines']['data'][0]['period']['end'], tz=timezone.get_fixed_timezone(0))
        subscription.status = Subscription.Status.ACTIVE
        subscription.save()

    except Subscription.DoesNotExist:
        logger.warning(f"Subscription {stripe_subscription_id} not found during invoice payment success")

@transaction.atomic
def _handle_subscription_deleted(subscription_data):
    """
    Handles subscription cancellation.
    """
    stripe_subscription_id = subscription_data.get('id')
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription_id)
        subscription.status = Subscription.Status.CANCELED
        subscription.save()
    except Subscription.DoesNotExist:
        logger.warning(f"Subscription {stripe_subscription_id} not found during deletion")

@transaction.atomic
def _handle_payment_failed(invoice):
    """
    Handles payment failure (Past Due).
    """
    stripe_subscription_id = invoice.get('subscription')
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription_id)
        subscription.status = Subscription.Status.PAST_DUE
        subscription.save()

        # Placeholder for notification
        print(f"NOTIFY: Payment failed for subscription {subscription.id} (User: {subscription.subscriber.email})")

    except Subscription.DoesNotExist:
        logger.warning(f"Subscription {stripe_subscription_id} not found during payment failure")
