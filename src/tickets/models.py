from django.db import models
from django.conf import settings
from core.models import TimeStampedModel
from sports.models import Match

class Ticket(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING_OCR = 'PENDING_OCR', 'Pending OCR'
        PROCESSING = 'PROCESSING', 'Processing'
        REVIEW_NEEDED = 'REVIEW_NEEDED', 'Review Needed'
        VALIDATED = 'VALIDATED', 'Validated'
        REJECTED = 'REJECTED', 'Rejected'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets')
    image = models.ImageField(upload_to='tickets/')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING_OCR)
    ocr_raw_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Ticket {self.id} - {self.status}"

class BetSelection(TimeStampedModel):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='selections')
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='bet_selections')
    selection = models.CharField(max_length=50) # e.g., "Home Win", "Over 2.5"
    odds = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.selection} @ {self.odds}"
