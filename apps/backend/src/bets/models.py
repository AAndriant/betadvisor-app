import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class BetTicket(models.Model):
    class BetStatus(models.TextChoices):
        PENDING = 'PENDING', _('En attente')
        WON = 'WON', _('Gagné')
        LOST = 'LOST', _('Perdu')
        VOID = 'VOID', _('Remboursé/Annulé')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bets')

    # Données du Pari
    match_title = models.CharField(max_length=255)
    selection = models.CharField(max_length=255)
    odds = models.DecimalField(max_digits=5, decimal_places=2) # Ex: 1.50
    stake = models.DecimalField(max_digits=10, decimal_places=2) # Mise

    # Preuve (Image pour OCR)
    ticket_image = models.ImageField(upload_to='tickets/%Y/%m/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    # Résultat
    status = models.CharField(max_length=10, choices=BetStatus.choices, default=BetStatus.PENDING)
    payout = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_premium = models.BooleanField(default=False)

    def calculate_payout(self):
        if self.status == self.BetStatus.WON:
            return self.stake * self.odds
        return 0

    def __str__(self):
        return f"{self.author} - {self.match_title} ({self.status})"
