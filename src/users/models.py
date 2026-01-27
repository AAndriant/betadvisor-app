from django.db import models
from django.contrib.auth.models import AbstractUser
from core.models import TimeStampedModel

class CustomUser(AbstractUser, TimeStampedModel):
    """
    Custom user model inheriting from AbstractUser and TimeStampedModel.
    """
    @property
    def is_tipster(self):
        return hasattr(self, 'tipster_profile')

class TipsterProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='tipster_profile')
    bio = models.TextField(blank=True)
    telegram_link = models.URLField(blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"Tipster: {self.user.username}"
