from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from subscriptions.models import Subscription

User = get_user_model()

class TipsterDashboardTests(APITestCase):
    def setUp(self):
        self.tipster = User.objects.create_user(username="tipster", email="t@t.com", password="p")
        self.follower1 = User.objects.create_user(username="f1", email="f1@t.com", password="p")
        self.follower2 = User.objects.create_user(username="f2", email="f2@t.com", password="p")
        self.url = reverse("my-dashboard")

    def test_dashboard_returns_correct_counts(self):
        self.client.force_authenticate(user=self.tipster)
        Subscription.objects.create(follower=self.follower1, tipster=self.tipster, stripe_subscription_id="sub_1", status="active")
        Subscription.objects.create(follower=self.follower2, tipster=self.tipster, stripe_subscription_id="sub_2", status="canceled")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["active_subscribers"], 1)
        self.assertEqual(response.data["total_subscribers_ever"], 2)

        # 1 active sub * 20 EUR * (1 - 0.20 platform fee) = 16.0
        self.assertEqual(response.data["monthly_revenue_estimate"], 16.0)
        self.assertEqual(len(response.data["recent_subscriptions"]), 1)

        recent_sub = response.data["recent_subscriptions"][0]
        self.assertEqual(recent_sub["follower_username"], "f1")
        self.assertEqual(recent_sub["status"], "active")
        self.assertIn("created_at", recent_sub)

    def test_dashboard_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dashboard_no_subscribers(self):
        self.client.force_authenticate(user=self.tipster)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["active_subscribers"], 0)
        self.assertEqual(response.data["total_subscribers_ever"], 0)
        self.assertEqual(response.data["monthly_revenue_estimate"], 0.0)
        self.assertEqual(len(response.data["recent_subscriptions"]), 0)
