from django.test import TestCase
from django.contrib.auth import get_user_model
from subscriptions.models import Subscription, StripeEvent

User = get_user_model()

class SubscriptionModelTest(TestCase):
    def test_str_method(self):
        follower = User.objects.create(username="follower", email="follower@example.com")
        tipster = User.objects.create(username="tipster", email="tipster@example.com")

        subscription = Subscription.objects.create(
            follower=follower,
            tipster=tipster,
            stripe_subscription_id="sub_12345",
            status="active"
        )

        self.assertEqual(str(subscription), "follower -> tipster (active)")

class StripeEventModelTest(TestCase):
    def test_str_method(self):
        event = StripeEvent.objects.create(
            stripe_event_id="evt_12345",
            event_type="invoice.payment_succeeded",
            payload={"id": "evt_12345", "type": "invoice.payment_succeeded"}
        )

        self.assertEqual(str(event), "Event evt_12345 (invoice.payment_succeeded)")
