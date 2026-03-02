import json
import os
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from connect.models import ConnectedAccount
from subscriptions.models import Subscription
import stripe

User = get_user_model()

class SubscriptionFlowTest(TestCase):
    def setUp(self):
        settings.STRIPE_SECRET_KEY = "sk_test_123"
        settings.STRIPE_WEBHOOK_SECRET = "whsec_test_secret"

        self.client = APIClient()
        self.follower = User.objects.create(username="follower", email="follower@example.com")
        self.tipster = User.objects.create(username="tipster", email="tipster@example.com")

        self.connected_account = ConnectedAccount.objects.create(
            user=self.tipster,
            stripe_account_id="acct_12345",
            charges_enabled=True,
            onboarding_completed=True
        )

        self.client.force_authenticate(user=self.follower)

    def _load_fixture(self, filename):
        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', filename)
        with open(fixture_path, 'r') as f:
            payload = json.load(f)
            return payload, json.dumps(payload).encode('utf-8')

    @patch('stripe.Webhook.construct_event')
    @patch('subscriptions.services.stripe.Customer.list')
    @patch('subscriptions.services.stripe.Customer.create')
    @patch('subscriptions.services.stripe.checkout.Session.create')
    def test_full_mobile_subscription_flow(self, mock_session_create, mock_customer_create, mock_customer_list, mock_construct_event):
        """
        Tests the end-to-end mobile flow for subscribing to a tipster:
        1. Call POST /api/connect/create-checkout-session/ to generate a checkout URL
        2. Simulate checkout completion via the Stripe webhook
        3. Verify the new subscription appears in GET /api/me/subscriptions/
        """

        # --- 1. POST /api/connect/create-checkout-session/ ---
        mock_customer_list.return_value = MagicMock(data=[])
        mock_customer_create.return_value = MagicMock(id="cus_test_123")
        mock_session_create.return_value = MagicMock(id="cs_test_123", url="http://example.com/checkout")

        subscribe_response = self.client.post('/api/connect/create-checkout-session/', {
            'tipster_id': self.tipster.id,
            'price_id': 'price_123'
        })

        self.assertEqual(subscribe_response.status_code, 200)
        self.assertEqual(subscribe_response.data['checkout_url'], "http://example.com/checkout")

        # --- 2. Simulate Webhook: checkout.session.completed ---
        payload, _ = self._load_fixture('checkout.session.completed.json')
        payload['data']['object']['metadata']['follower_id'] = str(self.follower.id)
        payload['data']['object']['metadata']['tipster_id'] = str(self.tipster.id)
        payload_bytes = json.dumps(payload).encode('utf-8')

        # Construct Stripe event
        event = stripe.Event.construct_from(payload, settings.STRIPE_SECRET_KEY)
        mock_construct_event.return_value = event

        # Send Webhook
        webhook_response = self.client.post(
            reverse('stripe-webhook'),
            data=payload_bytes,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=fake_signature'
        )

        self.assertEqual(webhook_response.status_code, 200)

        # Verify DB state directly first
        self.assertEqual(Subscription.objects.count(), 1)
        sub = Subscription.objects.first()
        self.assertEqual(sub.follower, self.follower)
        self.assertEqual(sub.tipster, self.tipster)
        self.assertEqual(sub.status, "active")
        self.assertEqual(sub.stripe_subscription_id, "sub_123")


        # --- 3. GET /api/me/subscriptions/ ---
        # my-subscriptions
        subscriptions_response = self.client.get(reverse('my-subscriptions'))

        self.assertEqual(subscriptions_response.status_code, 200)

        results = subscriptions_response.data
        if isinstance(results, dict) and 'results' in results:
            results = results['results']

        self.assertEqual(len(results), 1)
        self.assertEqual(str(results[0]['tipster']), str(self.tipster.id))
        self.assertEqual(results[0]['status'], 'active')
        # stripe_subscription_id is not included in SubscriptionSerializer, so no need to check it in response
        # It has already been verified in the DB state.
