from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch
from datetime import datetime, timezone
from subscriptions.models import Subscription, StripeEvent
from connect.models import ConnectedAccount
from subscriptions.webhooks import (
    _handle_checkout_session_completed,
    _handle_invoice_paid,
    _handle_invoice_payment_failed,
    _handle_customer_subscription_deleted,
    _handle_account_updated,
    _handle_stripe_event
)

User = get_user_model()

class TestWebhookCheckoutCompleted(APITestCase):
    def setUp(self):
        self.follower = User.objects.create_user(username="f", email="f@t.com", password="p")
        self.tipster = User.objects.create_user(username="t", email="t@t.com", password="p")
        self.event_base = {
            "id": "evt_test_123",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "mode": "subscription",
                    "metadata": {
                        "follower_id": str(self.follower.id),
                        "tipster_id": str(self.tipster.id)
                    },
                    "subscription": "sub_test_123",
                    "customer": "cus_test_123"
                }
            }
        }

    def test_creates_subscription_on_valid_event(self):
        _handle_stripe_event(self.event_base)

        sub = Subscription.objects.get(stripe_subscription_id="sub_test_123")
        self.assertEqual(sub.follower, self.follower)
        self.assertEqual(sub.tipster, self.tipster)
        self.assertEqual(sub.stripe_customer_id, "cus_test_123")
        self.assertEqual(sub.status, "active")

    def test_skips_non_subscription_mode(self):
        event = self.event_base.copy()
        event['data']['object']['mode'] = "payment"

        _handle_stripe_event(event)
        self.assertEqual(Subscription.objects.count(), 0)

    def test_missing_metadata_does_not_crash(self):
        event = self.event_base.copy()
        event['data']['object']['metadata'] = {}

        _handle_stripe_event(event)
        self.assertEqual(Subscription.objects.count(), 0)

    def test_idempotency_skips_duplicate_event(self):
        _handle_stripe_event(self.event_base)
        self.assertEqual(Subscription.objects.count(), 1)

        _handle_stripe_event(self.event_base)
        self.assertEqual(Subscription.objects.count(), 1)
        self.assertEqual(StripeEvent.objects.count(), 1)


class TestWebhookInvoicePaid(APITestCase):
    def setUp(self):
        self.follower = User.objects.create_user(username="f", email="f@t.com", password="p")
        self.tipster = User.objects.create_user(username="t", email="t@t.com", password="p")
        self.subscription = Subscription.objects.create(
            follower=self.follower,
            tipster=self.tipster,
            stripe_subscription_id="sub_test_456",
            status="past_due"
        )
        self.event_base = {
            "id": "evt_test_456",
            "type": "invoice.paid",
            "data": {
                "object": {
                    "id": "in_test_456",
                    "subscription": "sub_test_456",
                    "lines": {
                        "data": [
                            {
                                "type": "subscription",
                                "period": {
                                    "end": 1700000000
                                }
                            }
                        ]
                    }
                }
            }
        }

    def test_updates_subscription_status_and_period(self):
        _handle_stripe_event(self.event_base)

        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, "active")
        self.assertEqual(self.subscription.current_period_end, datetime.fromtimestamp(1700000000, tz=timezone.utc))

    def test_ignores_invoice_without_subscription_id(self):
        event = self.event_base.copy()
        event['data']['object'].pop('subscription', None)

        _handle_stripe_event(event)

        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, "past_due")


class TestWebhookInvoicePaymentFailed(APITestCase):
    def setUp(self):
        self.follower = User.objects.create_user(username="f", email="f@t.com", password="p")
        self.tipster = User.objects.create_user(username="t", email="t@t.com", password="p")
        self.subscription = Subscription.objects.create(
            follower=self.follower,
            tipster=self.tipster,
            stripe_subscription_id="sub_test_789",
            status="active"
        )
        self.event_base = {
            "id": "evt_test_789",
            "type": "invoice.payment_failed",
            "data": {
                "object": {
                    "id": "in_test_789",
                    "subscription": "sub_test_789"
                }
            }
        }

    def test_sets_status_past_due(self):
        _handle_stripe_event(self.event_base)

        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, "past_due")

class TestWebhookSubscriptionDeleted(APITestCase):
    def setUp(self):
        self.follower = User.objects.create_user(username="f", email="f@t.com", password="p")
        self.tipster = User.objects.create_user(username="t", email="t@t.com", password="p")
        self.subscription = Subscription.objects.create(
            follower=self.follower,
            tipster=self.tipster,
            stripe_subscription_id="sub_test_deleted",
            status="active"
        )
        self.event_base = {
            "id": "evt_test_del",
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_test_deleted"
                }
            }
        }

    def test_sets_status_canceled(self):
        _handle_stripe_event(self.event_base)

        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, "canceled")

class TestWebhookAccountUpdated(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u", email="u@t.com", password="p")
        self.connected_account = ConnectedAccount.objects.create(
            user=self.user,
            stripe_account_id="acct_test",
            charges_enabled=False,
            payouts_enabled=False,
            onboarding_completed=False
        )
        self.event_base = {
            "id": "evt_test_acct",
            "type": "account.updated",
            "data": {
                "object": {
                    "id": "acct_test",
                    "charges_enabled": True,
                    "payouts_enabled": False
                }
            }
        }

    def test_updates_connected_account_flags(self):
        _handle_stripe_event(self.event_base)

        self.connected_account.refresh_from_db()
        self.assertEqual(self.connected_account.charges_enabled, True)
        self.assertEqual(self.connected_account.payouts_enabled, False)
        self.assertEqual(self.connected_account.onboarding_completed, False)

    def test_sets_onboarding_completed_when_both_enabled(self):
        event = self.event_base.copy()
        event['data']['object']['payouts_enabled'] = True

        _handle_stripe_event(event)

        self.connected_account.refresh_from_db()
        self.assertEqual(self.connected_account.charges_enabled, True)
        self.assertEqual(self.connected_account.payouts_enabled, True)
        self.assertEqual(self.connected_account.onboarding_completed, True)

class TestStripeWebhookEndpoint(APITestCase):
    @patch("stripe.Webhook.construct_event")
    def test_valid_webhook_returns_200(self, mock_construct):
        event = {
            "id": "evt_test_ep",
            "type": "some.event",
            "data": {}
        }
        mock_construct.return_value = event

        response = self.client.post(
            reverse("stripe-webhook"),
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="sig_test"
        )
        self.assertEqual(response.status_code, 200)

    def test_missing_signature_returns_400(self):
        response = self.client.post(
            reverse("stripe-webhook"),
            data=b"{}",
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
