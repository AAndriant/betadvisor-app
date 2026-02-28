from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from bets.models import BetTicket
from decimal import Decimal

User = get_user_model()

class ApiTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='apiuser', password='password')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create some bets for stats
        BetTicket.objects.create(
            author=self.user,
            match_title="Match 1",
            selection="Win",
            odds=Decimal("2.00"),
            stake=Decimal("100.00"),
            status=BetTicket.BetStatus.WON
        )
        BetTicket.objects.create(
            author=self.user,
            match_title="Match 2",
            selection="Loss",
            odds=Decimal("2.00"),
            stake=Decimal("100.00"),
            status=BetTicket.BetStatus.LOST
        )

    def test_my_profile_stats(self):
        response = self.client.get('/api/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stats = response.data['stats']
        # Total bets: 2. Won: 1. Winrate: 50%.
        # Profit: (100*2 - 100) - 100 = 100 - 100 = 0.
        # ROI: 0 / 200 = 0.
        self.assertEqual(stats['total_bets'], 2)
        self.assertEqual(stats['win_rate'], 50.0)
        self.assertEqual(stats['total_profit'], 0.0)
        self.assertEqual(stats['roi'], 0.0)

    def test_create_bet_via_api(self):
        data = {
            'match_title': 'New Match',
            'selection': 'Draw',
            'odds': 3.50,
            'stake': 50.00,
            # ticket_image is optional or can be skipped for this test if generic
        }
        response = self.client.post('/api/bets/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BetTicket.objects.count(), 3)
        self.assertEqual(BetTicket.objects.last().author, self.user)

    def test_list_bets(self):
        response = self.client.get('/api/bets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should verify list length, etc.
        self.assertTrue(len(response.data['results']) >= 2)
