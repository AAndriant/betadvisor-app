from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import BetTicket
from decimal import Decimal

User = get_user_model()

class BetTicketTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')

    def test_create_bet_ticket(self):
        ticket = BetTicket.objects.create(
            author=self.user,
            match_title="Real Madrid vs Barcelona",
            selection="Home Win",
            odds=Decimal("1.50"),
            stake=Decimal("100.00"),
            status=BetTicket.BetStatus.PENDING
        )
        self.assertEqual(ticket.match_title, "Real Madrid vs Barcelona")
        self.assertEqual(ticket.stake, Decimal("100.00"))
        self.assertEqual(ticket.status, "PENDING")
