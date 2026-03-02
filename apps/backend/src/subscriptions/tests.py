from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch
from subscriptions.models import Subscription
from subscriptions.services import TipsterNotOnboardedError

User = get_user_model()

class SubscribeViewTests(APITestCase):
    def setUp(self):
        self.follower = User.objects.create_user(
            username='follower',
            email='follower@test.com',
            password='password123'
        )
        self.tipster = User.objects.create_user(
            username='tipster',
            email='tipster@test.com',
            password='password123'
        )
        self.url = reverse('subscribe')

    @patch('subscriptions.views.create_subscription_checkout')
    def test_subscribe_canonical_success(self, mock_create_checkout):
        """Test the canonical endpoint POST /api/subscriptions/subscribe/ successfully returns 200 + checkout_url payload."""
        self.client.force_authenticate(user=self.follower)
        mock_create_checkout.return_value = 'https://checkout.stripe.com/c/pay/cs_test_dummy'

        data = {'tipster_id': self.tipster.id}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'checkout_url': 'https://checkout.stripe.com/c/pay/cs_test_dummy'})
        mock_create_checkout.assert_called_once()
        args, kwargs = mock_create_checkout.call_args
        self.assertEqual(kwargs['follower'], self.follower)
        self.assertEqual(kwargs['tipster'], self.tipster)

    def test_subscribe_missing_tipster_id(self):
        """Test missing tipster_id returns 400 Bad Request."""
        self.client.force_authenticate(user=self.follower)
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'tipster_id is required'})

    @patch('subscriptions.views.create_subscription_checkout')
    def test_subscribe_tipster_not_onboarded(self, mock_create_checkout):
        """Test tipster not onboarded returns 400 Bad Request."""
        self.client.force_authenticate(user=self.follower)
        mock_create_checkout.side_effect = TipsterNotOnboardedError("Tipster not onboarded")

        data = {'tipster_id': self.tipster.id}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'Tipster not onboarded'})

    def test_subscribe_already_subscribed(self):
        """Test attempting to subscribe when already active returns 409 Conflict."""
        self.client.force_authenticate(user=self.follower)
        Subscription.objects.create(
            follower=self.follower,
            tipster=self.tipster,
            status='active'
        )

        data = {'tipster_id': self.tipster.id}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data, {'error': 'Active subscription already exists'})
