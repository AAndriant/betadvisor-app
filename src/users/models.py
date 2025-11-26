from django.contrib.auth.models import AbstractUser
from core.models import TimeStampedModel

class CustomUser(AbstractUser, TimeStampedModel):
    """
    Custom user model inheriting from AbstractUser and TimeStampedModel.
    """
    pass
