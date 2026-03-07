from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from connect.models import ConnectedAccount
from connect.services import (
    create_express_account,
    create_onboarding_link,
    StripeConnectError,
)

User = get_user_model()

STRIPE_TEST_SETTINGS = {
    'STRIPE_SECRET_KEY': 'sk_test_fake_key_for_unit_tests',
}


# ─────────────────────────────────────────────────────────────
# Tests for create_express_account
# ─────────────────────────────────────────────────────────────

@override_settings(**STRIPE_TEST_SETTINGS)
class CreateExpressAccountTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='tipster1',
            email='tipster1@test.com',
            password='password123'
        )

    @patch('connect.services.stripe.Account.create')
    def test_success_creates_account(self, mock_stripe_create):
        """Test successful Stripe Express account creation."""
        mock_stripe_create.return_value = MagicMock(id='acct_test_123')

        account = create_express_account(self.user)

        self.assertEqual(account.stripe_account_id, 'acct_test_123')
        self.assertEqual(account.user, self.user)
        mock_stripe_create.assert_called_once_with(type='express')

    @patch('connect.services.stripe.Account.create')
    def test_duplicate_account_raises_error(self, mock_stripe_create):
        """Test that creating a second account for the same user raises StripeConnectError."""
        ConnectedAccount.objects.create(
            user=self.user,
            stripe_account_id='acct_existing_456'
        )

        with self.assertRaises(StripeConnectError):
            create_express_account(self.user)

        mock_stripe_create.assert_not_called()

    @override_settings(STRIPE_SECRET_KEY='')
    def test_missing_api_key_raises_error(self):
        """Test that missing STRIPE_SECRET_KEY raises StripeConnectError."""
        with self.assertRaises(StripeConnectError) as ctx:
            create_express_account(self.user)
        self.assertIn('not configured', str(ctx.exception))

    @patch('connect.services.stripe.Account.create')
    def test_stripe_api_error_raises_error(self, mock_stripe_create):
        """Test that Stripe API errors are properly wrapped in StripeConnectError."""
        import stripe
        mock_stripe_create.side_effect = stripe.error.StripeError('Card declined')

        with self.assertRaises(StripeConnectError) as ctx:
            create_express_account(self.user)
        self.assertIn('Stripe error', str(ctx.exception))


# ─────────────────────────────────────────────────────────────
# Tests for create_onboarding_link
# ─────────────────────────────────────────────────────────────

@override_settings(**STRIPE_TEST_SETTINGS)
class CreateOnboardingLinkTests(TestCase):
    @patch('connect.services.stripe.AccountLink.create')
    def test_success_returns_url(self, mock_link_create):
        """Test successful onboarding link creation."""
        mock_link_create.return_value = MagicMock(url='https://connect.stripe.com/setup/abc')

        url = create_onboarding_link(
            stripe_account_id='acct_test_123',
            return_url='https://example.com/return',
            refresh_url='https://example.com/refresh',
        )

        self.assertEqual(url, 'https://connect.stripe.com/setup/abc')
        mock_link_create.assert_called_once_with(
            account='acct_test_123',
            refresh_url='https://example.com/refresh',
            return_url='https://example.com/return',
            type='account_onboarding',
        )

    @override_settings(STRIPE_SECRET_KEY='')
    def test_missing_api_key_raises_error(self):
        """Test that missing STRIPE_SECRET_KEY raises StripeConnectError."""
        with self.assertRaises(StripeConnectError) as ctx:
            create_onboarding_link('acct_test', 'http://r', 'http://x')
        self.assertIn('not configured', str(ctx.exception))

    @patch('connect.services.stripe.AccountLink.create')
    def test_stripe_api_error_raises_error(self, mock_link_create):
        """Test that Stripe API errors are properly wrapped in StripeConnectError."""
        import stripe
        mock_link_create.side_effect = stripe.error.StripeError('Invalid account')

        with self.assertRaises(StripeConnectError) as ctx:
            create_onboarding_link('acct_bad', 'http://r', 'http://x')
        self.assertIn('Stripe error', str(ctx.exception))

    @patch('connect.services.stripe.AccountLink.create')
    def test_unexpected_error_raises_error(self, mock_link_create):
        """Test that unexpected errors are properly wrapped in StripeConnectError."""
        mock_link_create.side_effect = RuntimeError('Network timeout')

        with self.assertRaises(StripeConnectError) as ctx:
            create_onboarding_link('acct_bad', 'http://r', 'http://x')
        self.assertIn('Unexpected error', str(ctx.exception))


# ─────────────────────────────────────────────────────────────
# Integration tests — Deprecated route (existing)
# ─────────────────────────────────────────────────────────────

class ConnectDeprecatedRouteTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='password123'
        )
        self.url = reverse('connect:create-checkout-session')

    def test_create_checkout_session_deprecated(self):
        """Test POST /api/connect/create-checkout-session/ returns 410 Gone."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        self.assertEqual(response.data, {'error': 'use /api/subscriptions/subscribe/'})
