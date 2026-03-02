from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from subscriptions.services import create_subscription_checkout, get_or_create_stripe_customer
from connect.models import ConnectedAccount
from django.conf import settings
from rest_framework.test import APIClient
from django.urls import reverse

User = get_user_model()

class SubscriptionServicesTest(TestCase):
    def setUp(self):
        settings.STRIPE_SECRET_KEY = "sk_test_123"
        self.follower = User.objects.create(username="follower", email="follower@example.com")
        self.tipster = User.objects.create(username="tipster", email="tipster@example.com")

        self.connected_account = ConnectedAccount.objects.create(
            user=self.tipster,
            stripe_account_id="acct_12345",
            charges_enabled=True,
            onboarding_completed=True
        )

    @patch('subscriptions.services.stripe.Customer.list')
    @patch('subscriptions.services.stripe.Customer.create')
    @patch('subscriptions.services.stripe.checkout.Session.create')
    def test_create_subscription_checkout_fee_placement(self, mock_session_create, mock_customer_create, mock_customer_list):
        # Setup mocks
        mock_customer_list.return_value = MagicMock(data=[MagicMock(id="cus_test_123")])
        mock_session_create.return_value = MagicMock(id="cs_test_123", url="http://example.com/checkout")

        url = create_subscription_checkout(
            follower=self.follower,
            tipster=self.tipster,
            price_id="price_123",
            success_url="http://example.com/success",
            cancel_url="http://example.com/cancel"
        )

        self.assertEqual(url, "http://example.com/checkout")

        # Verify call arguments
        mock_session_create.assert_called_once()
        _, kwargs = mock_session_create.call_args

        self.assertEqual(kwargs['mode'], 'subscription')
        self.assertNotIn('stripe_account', kwargs)

        # Verify application_fee_percent is passed correctly at Checkout Session level inside subscription_data
        self.assertIn('subscription_data', kwargs)
        self.assertIn('application_fee_percent', kwargs['subscription_data'])
        self.assertEqual(kwargs['subscription_data']['application_fee_percent'], 20)

        # It must contain transfer_data since we use Destination Charges for Subscriptions
        self.assertIn('transfer_data', kwargs['subscription_data'])
        self.assertEqual(kwargs['subscription_data']['transfer_data']['destination'], 'acct_12345')

class SubscribeViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.follower = User.objects.create(username="follower_view", email="follower_view@example.com")
        self.tipster = User.objects.create(username="tipster_view", email="tipster_view@example.com")
        self.client.force_authenticate(user=self.follower)

        # Give the tipster a connected account to pass the view logic
        self.connected_account = ConnectedAccount.objects.create(
            user=self.tipster,
            stripe_account_id="acct_123456",
            charges_enabled=True,
            onboarding_completed=True
        )

    @patch('subscriptions.views.create_subscription_checkout')
    def test_subscribe_uses_settings_urls_for_checkout(self, mock_create_checkout):
        """
        Verify that SubscribeView falls back to settings.CHECKOUT_SUCCESS_URL
        and settings.CHECKOUT_CANCEL_URL when success_url and cancel_url are
        not provided in the request payload.
        """
        mock_create_checkout.return_value = "http://example.com/checkout"

        # Override settings for the test
        with self.settings(CHECKOUT_SUCCESS_URL="http://test.com/success", CHECKOUT_CANCEL_URL="http://test.com/cancel"):
            response = self.client.post(reverse('subscribe'), {
                'tipster_id': self.tipster.id,
                'price_id': 'price_123'
            })

            self.assertEqual(response.status_code, 200)

            mock_create_checkout.assert_called_once()
            _, kwargs = mock_create_checkout.call_args

            self.assertEqual(kwargs['success_url'], "http://test.com/success")
            self.assertEqual(kwargs['cancel_url'], "http://test.com/cancel")
