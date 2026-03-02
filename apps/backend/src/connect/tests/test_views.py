from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.urls import reverse
from unittest.mock import patch
from connect.models import ConnectedAccount
from django.conf import settings

User = get_user_model()

class CreateConnectedAccountViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(username="testuser", email="test@example.com")

    def test_unauthenticated(self):
        response = self.client.post(reverse('connect:create-account'))
        self.assertEqual(response.status_code, 401)

    @patch('connect.views.create_express_account')
    def test_authenticated_creates_account(self, mock_create):
        self.client.force_authenticate(user=self.user)
        account = ConnectedAccount(
            user=self.user,
            stripe_account_id="acct_12345",
            charges_enabled=False,
            onboarding_completed=False
        )
        mock_create.return_value = account

        response = self.client.post(reverse('connect:create-account'))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['stripe_account_id'], "acct_12345")
        mock_create.assert_called_once_with(self.user)

class OnboardingLinkViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(username="testuser", email="test@example.com")
        self.client.force_authenticate(user=self.user)

        self.connected_account = ConnectedAccount.objects.create(
            user=self.user,
            stripe_account_id="acct_12345",
            charges_enabled=False,
            onboarding_completed=False
        )

    def test_unauthenticated(self):
        self.client.logout()
        # Force APIClient to be unauthenticated for this request
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse('connect:onboarding-link'))
        self.assertEqual(response.status_code, 401)

    @patch('connect.views.create_onboarding_link')
    def test_onboarding_link_uses_settings_urls(self, mock_create_onboarding_link):
        """
        Verify that OnboardingLinkView falls back to settings.ONBOARDING_RETURN_URL
        and settings.ONBOARDING_REFRESH_URL when constructing the onboarding link.
        """
        mock_create_onboarding_link.return_value = "https://connect.stripe.com/setup/s/mocked_link"

        with self.settings(ONBOARDING_RETURN_URL="http://test.com/onboard-return", ONBOARDING_REFRESH_URL="http://test.com/onboard-refresh"):
            response = self.client.get(reverse('connect:onboarding-link'))

            self.assertEqual(response.status_code, 200)

            mock_create_onboarding_link.assert_called_once()
            _, kwargs = mock_create_onboarding_link.call_args

            self.assertEqual(kwargs['return_url'], "http://test.com/onboard-return")
            self.assertEqual(kwargs['refresh_url'], "http://test.com/onboard-refresh")
