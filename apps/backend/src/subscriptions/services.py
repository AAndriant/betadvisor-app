import logging
import stripe
from decimal import Decimal
from django.conf import settings
from connect.models import ConnectedAccount
from users.models import TipsterProfile

logger = logging.getLogger(__name__)


class TipsterNotOnboardedError(Exception):
    pass


def get_or_create_stripe_customer(user) -> str:
    stripe.api_key = settings.STRIPE_SECRET_KEY
    if not stripe.api_key:
        logger.error("Missing STRIPE_SECRET_KEY")
        raise ValueError("Missing STRIPE_SECRET_KEY")

    customers = stripe.Customer.list(email=user.email)
    if customers.data:
        customer_id = customers.data[0].id
        logger.info(f"Found existing Stripe customer for user {user.email}: {customer_id}")
        return customer_id

    customer = stripe.Customer.create(email=user.email, metadata={'user_id': str(user.id)})
    logger.info(f"Created new Stripe customer for user {user.email}: {customer.id}")
    return customer.id


def get_or_create_tipster_price(tipster) -> str:
    """
    S8-05: Get or create a Stripe Price for this tipster's subscription.

    1. If the tipster already has a stripe_price_id, use it.
    2. Otherwise, create a new Stripe Product + Price and store the ID.
    3. Falls back to STRIPE_SUBSCRIPTION_PRICE_ID if tipster has no profile.
    """
    stripe.api_key = settings.STRIPE_SECRET_KEY

    # Check if tipster has a profile with pricing
    try:
        profile = tipster.tipster_profile
    except TipsterProfile.DoesNotExist:
        # Fallback to global price if no tipster profile
        fallback_price = settings.STRIPE_SUBSCRIPTION_PRICE_ID
        if fallback_price:
            return fallback_price
        raise ValueError("No tipster profile and no default STRIPE_SUBSCRIPTION_PRICE_ID configured.")

    # If already has a Stripe price, return it
    if profile.stripe_price_id:
        return profile.stripe_price_id

    # Create new Stripe Product + Price for this tipster
    price_cents = int(profile.subscription_price * 100)

    product = stripe.Product.create(
        name=f"Abonnement — {tipster.username}",
        metadata={'tipster_id': str(tipster.id)},
    )

    price = stripe.Price.create(
        unit_amount=price_cents,
        currency='eur',
        recurring={'interval': 'month'},
        product=product.id,
        metadata={'tipster_id': str(tipster.id)},
    )

    # Store the price ID for future use
    profile.stripe_price_id = price.id
    profile.save(update_fields=['stripe_price_id'])

    logger.info(
        f"Created Stripe price {price.id} for tipster {tipster.username} "
        f"at {profile.subscription_price} EUR/month"
    )

    return price.id


def create_subscription_checkout(follower, tipster, success_url, cancel_url) -> str:
    stripe.api_key = settings.STRIPE_SECRET_KEY
    if not stripe.api_key:
        logger.error("Missing STRIPE_SECRET_KEY")
        raise ValueError("Missing STRIPE_SECRET_KEY")

    # S8-05: Use dynamic tipster pricing instead of global price
    price_id = get_or_create_tipster_price(tipster)

    try:
        connected_account = tipster.connected_account
    except ConnectedAccount.DoesNotExist:
        logger.error(f"Tipster {tipster.id} has no connected account")
        raise TipsterNotOnboardedError("Tipster has no connected account")

    if not connected_account.charges_enabled or not connected_account.onboarding_completed:
        logger.error(f"Tipster {tipster.id} is not fully onboarded")
        raise TipsterNotOnboardedError("Tipster is not fully onboarded")

    stripe_customer_id = get_or_create_stripe_customer(follower)

    session = stripe.checkout.Session.create(
        mode='subscription',
        customer=stripe_customer_id,
        line_items=[{
            'price': price_id,
            'quantity': 1,
        }],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            'follower_id': str(follower.id),
            'tipster_id': str(tipster.id),
        },
        subscription_data={
            'metadata': {
                'follower_id': str(follower.id),
                'tipster_id': str(tipster.id)
            },
            'application_fee_percent': 20,
            'transfer_data': {
                'destination': connected_account.stripe_account_id
            }
        }
    )

    logger.info(f"Created checkout session {session.id} for follower {follower.id} to tipster {tipster.id}")
    return session.url


def cancel_subscription(subscription):
    """Cancel a subscription via Stripe API."""
    stripe.api_key = settings.STRIPE_SECRET_KEY
    if not stripe.api_key:
        raise ValueError("Missing STRIPE_SECRET_KEY")

    try:
        stripe.Subscription.cancel(subscription.stripe_subscription_id)
        subscription.status = 'canceled'
        subscription.save()
        logger.info(f"Canceled subscription {subscription.id} (stripe: {subscription.stripe_subscription_id})")
    except stripe.error.InvalidRequestError as e:
        logger.error(f"Stripe error canceling subscription: {e}")
        subscription.status = 'canceled'
        subscription.save()
