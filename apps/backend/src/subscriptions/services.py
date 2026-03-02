import logging
import stripe
from django.conf import settings
from connect.models import ConnectedAccount

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

def create_subscription_checkout(follower, tipster, price_id, success_url, cancel_url) -> str:
    stripe.api_key = settings.STRIPE_SECRET_KEY
    if not stripe.api_key:
        logger.error("Missing STRIPE_SECRET_KEY")
        raise ValueError("Missing STRIPE_SECRET_KEY")

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
        # For recurring payments (mode='subscription'), application_fee_percent MUST be inside subscription_data.
        # See Stripe API Reference: https://docs.stripe.com/api/checkout/sessions/create#create_checkout_session-subscription_data-application_fee_percent
    )

    logger.info(f"Created checkout session {session.id} for follower {follower.id} to tipster {tipster.id}")
    return session.url
