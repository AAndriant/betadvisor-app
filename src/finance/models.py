from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from core.models import TimeStampedModel

class Wallet(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal('0.0000'))

    def __str__(self):
        return f"Wallet of {self.user}"

class Transaction(TimeStampedModel):
    class Type(models.TextChoices):
        DEPOSIT = 'DEPOSIT', 'Deposit'
        SUBSCRIPTION = 'SUBSCRIPTION', 'Subscription'
        PAYOUT = 'PAYOUT', 'Payout'
        ADJUSTMENT = 'ADJUSTMENT', 'Adjustment'

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount_gross = models.DecimalField(max_digits=19, decimal_places=4)
    app_fee = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal('0.0000'))
    amount_net = models.DecimalField(max_digits=19, decimal_places=4)
    type = models.CharField(max_length=20, choices=Type.choices)

    def clean(self):
        # Validation rule: amount_gross = amount_net + app_fee
        # Using a small epsilon for float comparison is not needed for Decimal, exact match expected.
        if self.amount_gross != (self.amount_net + self.app_fee):
            raise ValidationError("Transaction integrity error: amount_gross must equal amount_net + app_fee")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.type} - {self.amount_gross}"


class StripeProfile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stripe_profile')
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    stripe_account_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    charges_enabled = models.BooleanField(default=False)

    def __str__(self):
        return f"StripeProfile for {self.user}"


class Plan(TimeStampedModel):
    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tipster = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='plans')
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.titre} ({self.price_amount})"


class Subscription(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        PAST_DUE = 'PAST_DUE', 'Past Due'
        CANCELED = 'CANCELED', 'Canceled'
        TRIALING = 'TRIALING', 'Trialing'

    subscriber = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='subscriptions')
    stripe_subscription_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices)
    current_period_end = models.DateTimeField(null=True, blank=True)
    platform_fee_percent = models.DecimalField(max_digits=5, decimal_places=2, help_text="Fee percent at the time of subscription")

    def __str__(self):
        return f"Subscription {self.stripe_subscription_id} - {self.status}"


class StripeEvent(TimeStampedModel):
    event_id = models.CharField(max_length=255, unique=True, db_index=True)
    type = models.CharField(max_length=255)
    processed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Event {self.event_id} ({self.type})"
