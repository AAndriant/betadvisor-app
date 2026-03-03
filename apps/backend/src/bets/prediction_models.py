from django.db import models
from django.conf import settings
from django.utils import timezone
from core.models import TimeStampedModel
from bets.models import BetTicket


class Prediction(TimeStampedModel):
    """
    A single prediction extracted from a tipster's bet ticket (post).
    The system automatically verifies predictions against real results
    via API-Sports / API-Tennis every 10 minutes.
    """

    class Outcome(models.TextChoices):
        PENDING = 'PENDING', 'En attente'
        CORRECT = 'CORRECT', 'Correct'
        INCORRECT = 'INCORRECT', 'Incorrect'
        VOID = 'VOID', 'Annulé'                # Match cancelled/postponed
        UNVERIFIABLE = 'UNVERIFIABLE', 'Non vérifiable'  # API can't verify this type

    class PredictionType(models.TextChoices):
        MATCH_RESULT = 'MATCH_RESULT', 'Résultat (1N2)'
        OVER_UNDER = 'OVER_UNDER', 'Over/Under'
        BTTS = 'BTTS', 'Les deux marquent'
        GOALSCORER = 'GOALSCORER', 'Buteur'
        DOUBLE_CHANCE = 'DOUBLE_CHANCE', 'Double chance'
        CORRECT_SCORE = 'CORRECT_SCORE', 'Score exact'
        WINNER = 'WINNER', 'Vainqueur'          # Tennis / MMA / generic
        SET_SCORE = 'SET_SCORE', 'Score en sets' # Tennis
        TOTAL_POINTS = 'TOTAL_POINTS', 'Total points'  # Basketball
        HANDICAP = 'HANDICAP', 'Handicap'
        OTHER = 'OTHER', 'Autre'

    class Sport(models.TextChoices):
        FOOTBALL = 'FOOTBALL', 'Football'
        TENNIS = 'TENNIS', 'Tennis'
        BASKETBALL = 'BASKETBALL', 'Basketball'
        RUGBY = 'RUGBY', 'Rugby'
        VOLLEYBALL = 'VOLLEYBALL', 'Volleyball'
        HANDBALL = 'HANDBALL', 'Handball'
        HOCKEY = 'HOCKEY', 'Hockey'
        BASEBALL = 'BASEBALL', 'Baseball'
        FORMULA1 = 'FORMULA1', 'Formule 1'
        MMA = 'MMA', 'MMA'

    # Link to the tipster's post
    bet_ticket = models.ForeignKey(
        BetTicket, on_delete=models.CASCADE, related_name='predictions'
    )

    # Prediction details (extracted by OCR)
    match_title = models.CharField(max_length=255)  # "PSG vs Real Madrid"
    sport = models.CharField(max_length=20, choices=Sport.choices, default=Sport.FOOTBALL)
    prediction_type = models.CharField(
        max_length=20, choices=PredictionType.choices, default=PredictionType.MATCH_RESULT
    )
    prediction_value = models.CharField(max_length=255)  # "Home Win", "Over 2.5", "Mbappé"

    # API linkage (populated after OCR extraction)
    api_fixture_id = models.IntegerField(null=True, blank=True, db_index=True)
    api_provider = models.CharField(
        max_length=20, blank=True, default='',
        help_text='api-sports or api-tennis'
    )
    api_match_date = models.DateTimeField(null=True, blank=True)

    # Resolution (populated by the cron settlement job)
    outcome = models.CharField(
        max_length=15, choices=Outcome.choices, default=Outcome.PENDING, db_index=True
    )
    actual_result = models.JSONField(
        null=True, blank=True,
        help_text='Raw result data from the sports API'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['outcome', 'api_fixture_id']),
        ]

    def resolve(self, outcome, actual_result=None):
        """Mark this prediction as resolved."""
        self.outcome = outcome
        self.actual_result = actual_result
        self.resolved_at = timezone.now()
        self.save()

    def __str__(self):
        return f"[{self.sport}] {self.match_title} — {self.prediction_value} ({self.outcome})"
