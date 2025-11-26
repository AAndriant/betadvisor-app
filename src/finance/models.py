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
