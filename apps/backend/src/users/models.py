from django.db import models
from django.contrib.auth.models import AbstractUser
from core.models import TimeStampedModel


class CustomUser(AbstractUser, TimeStampedModel):
    """
    Custom user model inheriting from AbstractUser and TimeStampedModel.
    """
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/',
        blank=True,
        null=True,
        help_text='User profile picture (max 5MB)'
    )
    bio = models.TextField(
        blank=True,
        default='',
        max_length=500,
        help_text='Short user biography (max 500 chars)'
    )

    @property
    def is_tipster(self):
        return hasattr(self, 'tipster_profile')

    @property
    def avatar_url(self):
        """Return real avatar URL or fallback to UI-Avatars."""
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return f"https://ui-avatars.com/api/?name={self.username}&background=10b981&color=fff"


class TipsterProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='tipster_profile')
    bio = models.TextField(blank=True)
    telegram_link = models.URLField(blank=True)
    is_verified = models.BooleanField(default=False)
    subscription_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=9.99,
        help_text='Monthly subscription price in EUR'
    )
    stripe_price_id = models.CharField(
        max_length=128,
        blank=True,
        default='',
        help_text='Stripe Price ID for this tipster (created dynamically)'
    )

    def __str__(self):
        return f"Tipster: {self.user.username}"
