from django.db import models
from django.conf import settings
from bets.models import BetTicket

class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes')
    bet = models.ForeignKey(BetTicket, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'bet')  # Un seul like par user/bet
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} liked {self.bet.id}"

class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    bet = models.ForeignKey(BetTicket, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} on {self.bet.id}: {self.content[:20]}"

class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following')
    followed = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.follower.username} follows {self.followed.username}"


class Report(models.Model):
    """Content/user flagging for moderation."""
    class Reason(models.TextChoices):
        SPAM = 'SPAM', 'Spam'
        INAPPROPRIATE = 'INAPPROPRIATE', 'Contenu inapproprié'
        FRAUD = 'FRAUD', 'Fraude / Faux résultats'
        HARASSMENT = 'HARASSMENT', 'Harcèlement'
        OTHER = 'OTHER', 'Autre'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'En attente'
        REVIEWED = 'REVIEWED', 'Examiné'
        DISMISSED = 'DISMISSED', 'Rejeté'
        ACTION_TAKEN = 'ACTION_TAKEN', 'Action prise'

    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_made')
    # Polymorphic target — one of these is set
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='reports_received', null=True, blank=True
    )
    reported_bet = models.ForeignKey(
        BetTicket, on_delete=models.CASCADE,
        related_name='reports', null=True, blank=True
    )
    reported_comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE,
        related_name='reports', null=True, blank=True
    )

    reason = models.CharField(max_length=20, choices=Reason.choices)
    details = models.TextField(blank=True, max_length=500)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        target = self.reported_user or self.reported_bet or self.reported_comment
        return f"Report by {self.reporter.username}: {self.reason} → {target}"
