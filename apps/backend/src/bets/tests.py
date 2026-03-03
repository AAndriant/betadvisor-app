from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework.test import APIRequestFactory
from .models import BetTicket
from .serializers import BetTicketSerializer
from decimal import Decimal
from django.apps import apps

User = get_user_model()
Subscription = apps.get_model('subscriptions', 'Subscription')

class BetPremiumGatingTests(APITestCase):
    def setUp(self):
        self.tipster = User.objects.create_user(username="tipster", email="t@t.com", password="p")
        self.subscriber = User.objects.create_user(username="sub", email="s@t.com", password="p")
        self.non_subscriber = User.objects.create_user(username="nonsub", email="ns@t.com", password="p")

        self.premium_bet = BetTicket.objects.create(
            author=self.tipster, is_premium=True,
            match_title="Premium Match", selection="Home Win",
            odds=Decimal("2.50"), stake=Decimal("10.00"),
            payout=Decimal("25.00"), status="PENDING"
        )
        self.non_premium_bet = BetTicket.objects.create(
            author=self.tipster, is_premium=False,
            match_title="Free Match", selection="Away Win",
            odds=Decimal("1.80"), stake=Decimal("5.00"),
            payout=Decimal("9.00"), status="PENDING"
        )

        Subscription.objects.create(
            follower=self.subscriber, tipster=self.tipster,
            stripe_subscription_id="sub_test_prem", status="active"
        )

    def test_subscriber_sees_full_premium_bet(self):
        self.client.force_authenticate(user=self.subscriber)
        response = self.client.get("/api/bets/")
        bet = response.data["results"][0] if "results" in response.data else response.data[0]
        # In our setup, we have 2 bets. We need to find the premium one.
        if "results" in response.data:
            bet = next(b for b in response.data["results"] if b["id"] == str(self.premium_bet.id))
        else:
            bet = next(b for b in response.data if b["id"] == str(self.premium_bet.id))

        self.assertEqual(bet["odds"], "2.50")
        self.assertFalse(bet.get("is_locked", False))

    def test_non_subscriber_sees_locked_premium_bet(self):
        self.client.force_authenticate(user=self.non_subscriber)
        response = self.client.get("/api/bets/")
        if "results" in response.data:
            bet = next(b for b in response.data["results"] if b["id"] == str(self.premium_bet.id))
        else:
            bet = next(b for b in response.data if b["id"] == str(self.premium_bet.id))

        self.assertIsNone(bet["odds"])
        self.assertIsNone(bet["stake"])
        self.assertIsNone(bet["payout"])
        self.assertTrue(bet["is_locked"])

    def test_unauthenticated_sees_locked_premium_bet(self):
        response = self.client.get("/api/bets/")
        # Unauthenticated users might get 401 on /api/bets/. If so, fallback to manual serializer testing,
        # but the issue says "Feed is served via GET /api/bets/".
        if response.status_code in [401, 403]:
            from django.contrib.auth.models import AnonymousUser
            factory = APIRequestFactory()
            request = factory.get('/')
            request.user = AnonymousUser()
            serializer = BetTicketSerializer(self.premium_bet, context={'request': request})
            bet = serializer.data
        else:
            if "results" in response.data:
                bet = next(b for b in response.data["results"] if b["id"] == str(self.premium_bet.id))
            else:
                bet = next(b for b in response.data if b["id"] == str(self.premium_bet.id))

        self.assertIsNone(bet["odds"])
        self.assertTrue(bet["is_locked"])

    def test_author_sees_full_premium_bet(self):
        self.client.force_authenticate(user=self.tipster)
        response = self.client.get("/api/bets/")
        if "results" in response.data:
            bet = next(b for b in response.data["results"] if b["id"] == str(self.premium_bet.id))
        else:
            bet = next(b for b in response.data if b["id"] == str(self.premium_bet.id))

        self.assertEqual(bet["odds"], "2.50")
        self.assertFalse(bet.get("is_locked", False))

    def test_non_premium_bet_always_visible(self):
        self.client.force_authenticate(user=self.non_subscriber)
        response = self.client.get("/api/bets/")
        if "results" in response.data:
            bet = next(b for b in response.data["results"] if b["id"] == str(self.non_premium_bet.id))
        else:
            bet = next(b for b in response.data if b["id"] == str(self.non_premium_bet.id))

        self.assertEqual(bet["odds"], "1.80")
        self.assertFalse(bet.get("is_locked", False))

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


class BetSettlementTests(APITestCase):
    def setUp(self):
        self.tipster = User.objects.create_user(username="tipster", email="t@t.com", password="p")
        self.other_user = User.objects.create_user(username="other", email="o@t.com", password="p")
        self.bet = BetTicket.objects.create(
            author=self.tipster,
            match_title="PSG vs Real Madrid",
            selection="PSG Win",
            odds=Decimal("2.50"),
            stake=Decimal("10.00"),
            status=BetTicket.BetStatus.PENDING
        )

    def test_settle_won(self):
        self.client.force_authenticate(user=self.tipster)
        response = self.client.post(f"/api/bets/{self.bet.id}/settle/", {"outcome": "WON"})
        self.assertEqual(response.status_code, 200)
        self.bet.refresh_from_db()
        self.assertEqual(self.bet.status, "WON")
        self.assertEqual(self.bet.payout, Decimal("25.00"))
        self.assertIsNotNone(self.bet.settled_at)

    def test_settle_lost(self):
        self.client.force_authenticate(user=self.tipster)
        response = self.client.post(f"/api/bets/{self.bet.id}/settle/", {"outcome": "LOST"})
        self.assertEqual(response.status_code, 200)
        self.bet.refresh_from_db()
        self.assertEqual(self.bet.status, "LOST")
        self.assertEqual(self.bet.payout, 0)

    def test_settle_void(self):
        self.client.force_authenticate(user=self.tipster)
        response = self.client.post(f"/api/bets/{self.bet.id}/settle/", {"outcome": "VOID"})
        self.assertEqual(response.status_code, 200)
        self.bet.refresh_from_db()
        self.assertEqual(self.bet.status, "VOID")

    def test_settle_forbidden_for_non_author(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(f"/api/bets/{self.bet.id}/settle/", {"outcome": "WON"})
        self.assertEqual(response.status_code, 403)

    def test_settle_already_settled(self):
        self.bet.settle("WON")
        self.client.force_authenticate(user=self.tipster)
        response = self.client.post(f"/api/bets/{self.bet.id}/settle/", {"outcome": "LOST"})
        self.assertEqual(response.status_code, 400)

    def test_settle_invalid_outcome(self):
        self.client.force_authenticate(user=self.tipster)
        response = self.client.post(f"/api/bets/{self.bet.id}/settle/", {"outcome": "INVALID"})
        self.assertEqual(response.status_code, 400)

    def test_settle_updates_gamification_stats(self):
        self.client.force_authenticate(user=self.tipster)
        self.client.post(f"/api/bets/{self.bet.id}/settle/", {"outcome": "WON"})

        from gamification.models import UserGlobalStats
        stats = UserGlobalStats.objects.get(user=self.tipster)
        self.assertEqual(stats.total_bets, 1)
        self.assertEqual(stats.wins, 1)
        self.assertEqual(stats.current_streak, 1)
