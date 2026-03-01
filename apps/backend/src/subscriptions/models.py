from django.db import models

class Subscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('incomplete', 'Incomplete'),
    ]

    follower = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='subscriptions_as_follower')
    tipster = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='subscriptions_as_tipster')
    stripe_subscription_id = models.CharField(max_length=128, unique=True)
    stripe_customer_id = models.CharField(max_length=64, blank=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=20)
    current_period_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('follower', 'tipster')

    def __str__(self):
        return f"{self.follower.username} -> {self.tipster.username} ({self.status})"

class StripeEvent(models.Model):
    stripe_event_id = models.CharField(max_length=64, unique=True)
    event_type = models.CharField(max_length=64)
    processed_at = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField()

    def __str__(self):
        return f"Event {self.stripe_event_id} ({self.event_type})"
