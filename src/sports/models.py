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
    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        LIVE = 'LIVE', 'Live'
        FINISHED = 'FINISHED', 'Finished'
        POSTPONED = 'POSTPONED', 'Postponed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='matches')
    home_team = models.CharField(max_length=100)
    away_team = models.CharField(max_length=100)
    date_time = models.DateTimeField(db_index=True)
    
    # Settlement module fields
    home_score = models.IntegerField(null=True, blank=True, help_text='Final score for home team')
    away_score = models.IntegerField(null=True, blank=True, help_text='Final score for away team')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    external_id = models.CharField(
        max_length=255, 
        unique=True, 
        null=True, 
        blank=True, 
        db_index=True,
        help_text='External API identifier for this match'
    )

    class Meta:
        verbose_name_plural = "Matches"

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} ({self.date_time})"
