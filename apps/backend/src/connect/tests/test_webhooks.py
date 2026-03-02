import json
import os
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
import stripe
from connect.models import ConnectedAccount
from subscriptions.models import StripeEvent

User = get_user_model()

class WebhookIdempotencyTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(username="testuser", email="test@example.com")
        self.connected_account = ConnectedAccount.objects.create(
            user=self.user,
            stripe_account_id="acct_1testaccount",
            charges_enabled=False,
            payouts_enabled=False,
            onboarding_completed=False
        )

        # Load fixture
        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'account.updated.json')
        with open(fixture_path, 'r') as f:
            self.account_updated_payload = json.load(f)
            self.payload_bytes = json.dumps(self.account_updated_payload).encode('utf-8')

        settings.STRIPE_WEBHOOK_SECRET = "whsec_test_secret"

    @patch('stripe.Webhook.construct_event')
    def test_account_updated_idempotency(self, mock_construct_event):
        # Setup mock to return the parsed event
        mock_construct_event.return_value = self.account_updated_payload

        # Send the event once -> verify state change
        response = self.client.post(
            reverse('stripe-webhook'),
            data=self.payload_bytes,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=fake_signature'
        )
        self.assertEqual(response.status_code, 200)

        # Refresh from db
        self.connected_account.refresh_from_db()
        self.assertTrue(self.connected_account.charges_enabled)
        self.assertTrue(self.connected_account.payouts_enabled)
        self.assertTrue(self.connected_account.onboarding_completed)
        self.assertEqual(StripeEvent.objects.count(), 1)

        # Send the exact same event again -> verify no duplicate, no crash, same final state
        response2 = self.client.post(
            reverse('stripe-webhook'),
            data=self.payload_bytes,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=fake_signature'
        )
        self.assertEqual(response2.status_code, 200)

        self.connected_account.refresh_from_db()
        self.assertTrue(self.connected_account.charges_enabled)
        self.assertTrue(self.connected_account.payouts_enabled)
        self.assertTrue(self.connected_account.onboarding_completed)
        # Verify no duplicate StripeEvent was created
        self.assertEqual(StripeEvent.objects.count(), 1)

    @patch('stripe.Webhook.construct_event')
    def test_webhook_signature_verification_checked(self, mock_construct_event):
        # Make the mock raise a SignatureVerificationError
        mock_construct_event.side_effect = stripe.error.SignatureVerificationError(
            message="Invalid signature",
            sig_header="v1=fake",
            http_body=self.payload_bytes
        )

        response = self.client.post(
            reverse('stripe-webhook'),
            data=self.payload_bytes,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=fake_signature'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b"Invalid signature")

        # Verify no state changes happened
        self.connected_account.refresh_from_db()
        self.assertFalse(self.connected_account.charges_enabled)
        self.assertEqual(StripeEvent.objects.count(), 0)
