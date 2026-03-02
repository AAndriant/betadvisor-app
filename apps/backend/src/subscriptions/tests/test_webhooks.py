import json
import os
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
import stripe
from subscriptions.models import Subscription, StripeEvent

User = get_user_model()

class SubscriptionWebhookIdempotencyTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.follower = User.objects.create(username="follower", email="follower@example.com")
        self.tipster = User.objects.create(username="tipster", email="tipster@example.com")

        settings.STRIPE_WEBHOOK_SECRET = "whsec_test_secret"

    def _load_fixture(self, filename):
        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', filename)
        with open(fixture_path, 'r') as f:
            payload = json.load(f)
            return payload, json.dumps(payload).encode('utf-8')

    @patch('stripe.Webhook.construct_event')
    def test_checkout_session_completed_idempotency(self, mock_construct_event):
        payload, _ = self._load_fixture('checkout.session.completed.json')
        # Inject correct UUIDs into payload
        payload['data']['object']['metadata']['follower_id'] = str(self.follower.id)
        payload['data']['object']['metadata']['tipster_id'] = str(self.tipster.id)
        payload_bytes = json.dumps(payload).encode('utf-8')
        mock_construct_event.return_value = payload

        # Send once
        response = self.client.post(
            reverse('stripe-webhook'),
            data=payload_bytes,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=fake_signature'
        )
        self.assertEqual(response.status_code, 200)

        # Verify created
        self.assertEqual(Subscription.objects.count(), 1)
        sub = Subscription.objects.get()
        self.assertEqual(sub.follower, self.follower)
        self.assertEqual(sub.tipster, self.tipster)
        self.assertEqual(sub.stripe_subscription_id, "sub_123")
        self.assertEqual(sub.stripe_customer_id, "cus_123")
        self.assertEqual(sub.status, "active")
        self.assertEqual(StripeEvent.objects.count(), 1)

        # Send again
        response2 = self.client.post(
            reverse('stripe-webhook'),
            data=payload_bytes,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=fake_signature'
        )
        self.assertEqual(response2.status_code, 200)

        # Verify no duplicate
        self.assertEqual(Subscription.objects.count(), 1)
        self.assertEqual(StripeEvent.objects.count(), 1)

    @patch('stripe.Webhook.construct_event')
    def test_customer_subscription_created_idempotency(self, mock_construct_event):
        payload, payload_bytes = self._load_fixture('customer.subscription.created.json')
        mock_construct_event.return_value = payload

        # Send once (this event has no handler currently, but should not crash)
        response = self.client.post(
            reverse('stripe-webhook'),
            data=payload_bytes,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=fake_signature'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(StripeEvent.objects.count(), 0)

        # Send again
        response2 = self.client.post(
            reverse('stripe-webhook'),
            data=payload_bytes,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=fake_signature'
        )
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(StripeEvent.objects.count(), 0)

    @patch('stripe.Webhook.construct_event')
    def test_customer_subscription_updated_idempotency(self, mock_construct_event):
        payload, payload_bytes = self._load_fixture('customer.subscription.updated.json')
        mock_construct_event.return_value = payload

        # Send once (no handler currently, no crash)
        response = self.client.post(
            reverse('stripe-webhook'),
            data=payload_bytes,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=fake_signature'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(StripeEvent.objects.count(), 0)

        # Send again
        response2 = self.client.post(
            reverse('stripe-webhook'),
            data=payload_bytes,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=fake_signature'
        )
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(StripeEvent.objects.count(), 0)

    @patch('stripe.Webhook.construct_event')
    def test_customer_subscription_deleted_idempotency(self, mock_construct_event):
        # Create subscription first
        sub = Subscription.objects.create(
            follower=self.follower,
            tipster=self.tipster,
            stripe_subscription_id="sub_123",
            stripe_customer_id="cus_123",
            status="active"
        )

        payload, payload_bytes = self._load_fixture('customer.subscription.deleted.json')
        mock_construct_event.return_value = payload

        # Send once
        response = self.client.post(
            reverse('stripe-webhook'),
            data=payload_bytes,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=fake_signature'
        )
        self.assertEqual(response.status_code, 200)

        sub.refresh_from_db()
        self.assertEqual(sub.status, "canceled")
        self.assertEqual(StripeEvent.objects.count(), 1)

        # Send again
        response2 = self.client.post(
            reverse('stripe-webhook'),
            data=payload_bytes,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=fake_signature'
        )
        self.assertEqual(response2.status_code, 200)

        sub.refresh_from_db()
        self.assertEqual(sub.status, "canceled")
        self.assertEqual(StripeEvent.objects.count(), 1)

    @patch('stripe.Webhook.construct_event')
    def test_webhook_signature_verification_checked(self, mock_construct_event):
        payload, payload_bytes = self._load_fixture('checkout.session.completed.json')
        mock_construct_event.side_effect = stripe.error.SignatureVerificationError(
            message="Invalid signature",
            sig_header="v1=fake",
            http_body=payload_bytes
        )

        response = self.client.post(
            reverse('stripe-webhook'),
            data=payload_bytes,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=fake_signature'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b"Invalid signature")
        self.assertEqual(Subscription.objects.count(), 0)
        self.assertEqual(StripeEvent.objects.count(), 0)
