from django.db import models
from core.models import TimeStampedModel

class Sport(TimeStampedModel):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class League(TimeStampedModel):
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='leagues')
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name

class Match(TimeStampedModel):
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='matches')
    home_team = models.CharField(max_length=100)
    away_team = models.CharField(max_length=100)
    date_time = models.DateTimeField(db_index=True)

    class Meta:
        verbose_name_plural = "Matches"

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} ({self.date_time})"
