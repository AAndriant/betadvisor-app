from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import CustomUser
from connect.models import ConnectedAccount
from unittest.mock import patch

class SubscribeViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.follower = CustomUser.objects.create_user(username='follower', password='password')
        self.tipster = CustomUser.objects.create_user(username='tipster', password='password')

        # Setup tipster connected account
        self.connected_account = ConnectedAccount.objects.create(
            user=self.tipster,
            stripe_account_id='acct_123456789',
            charges_enabled=True,
            onboarding_completed=True
        )

        self.client.force_authenticate(user=self.follower)
        self.url = reverse('subscribe')

    @override_settings(STRIPE_SUBSCRIPTION_PRICE_ID='')
    def test_subscribe_missing_price_id(self):
        response = self.client.post(self.url, {'tipster_id': self.tipster.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'System misconfigured: STRIPE_SUBSCRIPTION_PRICE_ID is missing')

    @override_settings(STRIPE_SUBSCRIPTION_PRICE_ID='price_12345')
    @patch('subscriptions.views.create_subscription_checkout')
    def test_subscribe_with_price_id(self, mock_create_checkout):
        mock_create_checkout.return_value = 'https://checkout.stripe.com/c/pay/cs_test_123'

        response = self.client.post(self.url, {'tipster_id': self.tipster.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['checkout_url'], 'https://checkout.stripe.com/c/pay/cs_test_123')

        # Verify the mock was called with the correct price_id from settings
        mock_create_checkout.assert_called_once()
        args, kwargs = mock_create_checkout.call_args
        self.assertEqual(kwargs['price_id'], 'price_12345')
