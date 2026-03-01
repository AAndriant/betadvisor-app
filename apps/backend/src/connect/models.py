from django.conf import settings
from django.db import models
from core.models import TimeStampedModel

class ConnectedAccount(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='connected_account')
    stripe_account_id = models.CharField(max_length=64, unique=True)
    charges_enabled = models.BooleanField(default=False)
    payouts_enabled = models.BooleanField(default=False)
    onboarding_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} — {self.stripe_account_id}"
