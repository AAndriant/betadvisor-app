import stripe
from django.conf import settings
from decimal import Decimal
from django.urls import reverse

stripe.api_key = settings.STRIPE_SECRET_KEY

from .models import StripeProfile

def create_connect_account(user):
    """
    Creates a Stripe Express account for the user and returns the account onboarding link.
    """
    profile, created = StripeProfile.objects.get_or_create(user=user)

    if not profile.stripe_account_id:
        account = stripe.Account.create(
            type="express",
            country="FR",  # Assuming France based on context ("BetAdvisor", "Siren", etc) or configurable
            email=user.email,
            capabilities={
                "card_payments": {"requested": True},
                "transfers": {"requested": True},
            },
        )
        profile.stripe_account_id = account.id
        profile.save()

    account_link = stripe.AccountLink.create(
        account=profile.stripe_account_id,
        refresh_url=f"{settings.SITE_URL}/finance/connect/refresh", # Placeholder
        return_url=f"{settings.SITE_URL}/finance/connect/return",   # Placeholder
        type="account_onboarding",
    )

    return account_link.url

def create_checkout_session(user, plan):
    """
    Creates a checkout session for a subscription plan.
    Calculates application fee based on the platform fee percent.
    """
    profile, created = StripeProfile.objects.get_or_create(user=user)
    if not profile.stripe_customer_id:
        customer = stripe.Customer.create(email=user.email, metadata={"user_id": str(user.id)})
        profile.stripe_customer_id = customer.id
        profile.save()

    # Calculate application fee
    # Stripe expects integers (cents)
    # price_cents = int(plan.price_amount * 100)
    fee_percent = settings.PLATFORM_FEE_PERCENT
    # application_fee_amount = int(price_cents * (fee_percent / 100)) # Unused, relying on percentage

    session = stripe.checkout.Session.create(
        customer=profile.stripe_customer_id,
        payment_method_types=["card"],
        line_items=[
            {
                "price": plan.stripe_price_id,
                "quantity": 1,
            },
        ],
        mode="subscription",
        subscription_data={
            "application_fee_percent": fee_percent, # Or use transfer_data with application_fee_amount if destination charges
            "metadata": {
                "user_id": str(user.id),
                "plan_id": str(plan.id),
                "platform_fee_percent": str(fee_percent)
            },
            "transfer_data": {
                "destination": plan.tipster.stripe_profile.stripe_account_id,
            }
        },
        success_url=f"{settings.SITE_URL}/finance/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.SITE_URL}/finance/cancel",
    )
    return session.url

def create_portal_session(user):
    """
    Creates a billing portal session for the user to manage subscriptions.
    """
    profile, created = StripeProfile.objects.get_or_create(user=user)
    if not profile.stripe_customer_id:
        raise ValueError("User does not have a Stripe Customer ID")

    session = stripe.billing_portal.Session.create(
        customer=profile.stripe_customer_id,
        return_url=f"{settings.SITE_URL}/dashboard",
    )
    return session.url
