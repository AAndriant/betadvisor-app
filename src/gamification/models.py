from decimal import Decimal
from django.db import models
from django.conf import settings
from core.models import TimeStampedModel
from sports.models import Sport

class UserGlobalStats(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='global_stats')
    total_bets = models.PositiveIntegerField(default=0)
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    voids = models.PositiveIntegerField(default=0)
    current_win_streak = models.PositiveIntegerField(default=0)
    max_win_streak = models.PositiveIntegerField(default=0)
    total_investment = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal('0.0000'))
    total_return = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal('0.0000'))

    @property
    def winrate(self):
        denominator = self.total_bets - self.voids
        if denominator > 0:
            return (self.wins / denominator) * 100
        return 0.0

    @property
    def roi(self):
        if self.total_investment > 0:
            return ((self.total_return - self.total_investment) / self.total_investment) * 100
        return 0.0

    def __str__(self):
        return f"Global Stats for {self.user}"

class UserSportStats(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sport_stats')
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='user_stats')
    total_bets = models.PositiveIntegerField(default=0)
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    voids = models.PositiveIntegerField(default=0)
    current_win_streak = models.PositiveIntegerField(default=0)
    max_win_streak = models.PositiveIntegerField(default=0)
    total_investment = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal('0.0000'))
    total_return = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal('0.0000'))

    class Meta:
        unique_together = ('user', 'sport')

    @property
    def winrate(self):
        denominator = self.total_bets - self.voids
        if denominator > 0:
            return (self.wins / denominator) * 100
        return 0.0

    @property
    def roi(self):
        if self.total_investment > 0:
            return ((self.total_return - self.total_investment) / self.total_investment) * 100
        return 0.0

    def __str__(self):
        return f"{self.sport} Stats for {self.user}"

class UserBadge(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='badges')
    badge_name = models.CharField(max_length=100)
    awarded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ('user', 'badge_name')

    def __str__(self):
        return f"{self.badge_name} - {self.user}"
