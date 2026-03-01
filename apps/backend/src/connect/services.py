import logging
import stripe
from django.conf import settings
from connect.models import ConnectedAccount
from django.db import transaction

logger = logging.getLogger(__name__)

class StripeConnectError(Exception):
    """Custom exception for Stripe Connect operations."""
    pass

def create_express_account(user):
    """
    Creates a Stripe Express account for the given user.
    Saves a ConnectedAccount model instance with the returned stripe_account_id.
    Raises StripeConnectError if the user already has a ConnectedAccount.
    """
    if not settings.STRIPE_SECRET_KEY:
        logger.error("Missing STRIPE_SECRET_KEY in settings.")
        raise StripeConnectError("Stripe is not configured properly.")

    # Guard to prevent creating multiple accounts for the same user
    if hasattr(user, 'connected_account'):
        raise StripeConnectError(f"User {user.id} already has a ConnectedAccount.")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        with transaction.atomic():
            # Check DB again within transaction if needed, but hasattr is usually enough for a quick check.
            # Using get_or_create or select_for_update might be better if there are concurrency issues.
            if ConnectedAccount.objects.filter(user=user).exists():
                raise StripeConnectError(f"User {user.id} already has a ConnectedAccount.")

            account = stripe.Account.create(type='express')
            stripe_account_id = account.id

            connected_account = ConnectedAccount.objects.create(
                user=user,
                stripe_account_id=stripe_account_id
            )

            logger.info(f"Successfully created Stripe Express account for user {user.id}: {stripe_account_id}")
            return connected_account
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating express account for user {user.id}: {str(e)}")
        raise StripeConnectError(f"Stripe error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error creating express account for user {user.id}: {str(e)}")
        raise StripeConnectError(f"Unexpected error: {str(e)}")

def create_onboarding_link(stripe_account_id, return_url, refresh_url):
    """
    Creates a Stripe AccountLink for onboarding.
    Returns the onboarding URL.
    """
    if not settings.STRIPE_SECRET_KEY:
        logger.error("Missing STRIPE_SECRET_KEY in settings.")
        raise StripeConnectError("Stripe is not configured properly.")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        account_link = stripe.AccountLink.create(
            account=stripe_account_id,
            refresh_url=refresh_url,
            return_url=return_url,
            type='account_onboarding',
        )
        logger.info(f"Successfully created onboarding link for account {stripe_account_id}")
        return account_link.url
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating onboarding link for account {stripe_account_id}: {str(e)}")
        raise StripeConnectError(f"Stripe error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error creating onboarding link for account {stripe_account_id}: {str(e)}")
        raise StripeConnectError(f"Unexpected error: {str(e)}")
