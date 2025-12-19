from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.conf import settings
from unittest.mock import patch, MagicMock
from decimal import Decimal
from .models import StripeProfile, Plan, Subscription, StripeEvent
from .services import create_connect_account, create_checkout_session, create_portal_session
from .webhooks import handle_stripe_webhook
import json

User = get_user_model()

class FinanceServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        self.tipster = User.objects.create_user(username='tipster', email='tipster@example.com', password='password')

        # StripeProfile is now created via signal, so we fetch it instead of creating
        self.user_profile = self.user.stripe_profile
        self.tipster_profile = self.tipster.stripe_profile
        self.tipster_profile.stripe_account_id = 'acct_test'
        self.tipster_profile.save()

        self.plan = Plan.objects.create(
            titre="Test Plan",
            price_amount=Decimal("10.00"),
            tipster=self.tipster,
            stripe_price_id="price_test"
        )

    @patch('stripe.Account.create')
    @patch('stripe.AccountLink.create')
    def test_create_connect_account(self, mock_link_create, mock_account_create):
        mock_account_create.return_value = MagicMock(id='acct_new')
        mock_link_create.return_value = MagicMock(url='http://test.com/onboard')

        url = create_connect_account(self.user)

        self.assertEqual(url, 'http://test.com/onboard')
        self.user.refresh_from_db()
        self.assertEqual(self.user.stripe_profile.stripe_account_id, 'acct_new')

    @patch('stripe.Account.create')
    @patch('stripe.AccountLink.create')
    def test_create_connect_account_no_profile(self, mock_link_create, mock_account_create):
        # Test user without profile (simulate existing user before migration/signal)
        user_no_prof = User.objects.create_user(username='noprof', email='no@example.com', password='password')
        # Manually delete profile created by signal if any
        if hasattr(user_no_prof, 'stripe_profile'):
            user_no_prof.stripe_profile.delete()

        mock_account_create.return_value = MagicMock(id='acct_fresh')
        mock_link_create.return_value = MagicMock(url='http://test.com/fresh')

        url = create_connect_account(user_no_prof)

        self.assertEqual(url, 'http://test.com/fresh')
        user_no_prof.refresh_from_db()
        self.assertTrue(hasattr(user_no_prof, 'stripe_profile'))
        self.assertEqual(user_no_prof.stripe_profile.stripe_account_id, 'acct_fresh')

    @patch('stripe.Customer.create')
    @patch('stripe.checkout.Session.create')
    def test_create_checkout_session(self, mock_session_create, mock_customer_create):
        mock_customer_create.return_value = MagicMock(id='cus_test')
        mock_session_create.return_value = MagicMock(url='http://test.com/checkout')

        url = create_checkout_session(self.user, self.plan)

        self.assertEqual(url, 'http://test.com/checkout')
        self.user.refresh_from_db()
        self.assertEqual(self.user.stripe_profile.stripe_customer_id, 'cus_test')

        # Verify fee calculation
        args, kwargs = mock_session_create.call_args
        self.assertEqual(kwargs['subscription_data']['application_fee_percent'], settings.PLATFORM_FEE_PERCENT)

class FinanceWebhookTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='subscriber', email='sub@example.com', password='password')
        self.tipster = User.objects.create_user(username='tipster', email='tip@example.com', password='password')
        # Profile created by signal, update it
        self.stripe_profile = self.user.stripe_profile
        self.stripe_profile.stripe_customer_id = 'cus_test'
        self.stripe_profile.save()

        self.plan = Plan.objects.create(
            titre="Test Plan",
            price_amount=Decimal("20.00"),
            tipster=self.tipster,
            stripe_price_id="price_test"
        )

    @patch('stripe.Webhook.construct_event')
    @patch('stripe.Subscription.retrieve')
    def test_webhook_idempotency(self, mock_sub_retrieve, mock_construct_event):
        # Mock payload
        payload = {
            'id': 'evt_test_123',
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'mode': 'subscription',
                    'subscription': 'sub_test',
                    'subscription_data': {
                        'metadata': {
                            'user_id': str(self.user.id),
                            'plan_id': str(self.plan.id)
                        }
                    }
                }
            }
        }

        mock_construct_event.return_value = payload
        mock_sub_retrieve.return_value = MagicMock(
            current_period_end=1700000000,
            metadata={'user_id': str(self.user.id), 'plan_id': str(self.plan.id), 'platform_fee_percent': '10.00'}
        )

        # First call
        handle_stripe_webhook(json.dumps(payload), 'sig')
        self.assertEqual(StripeEvent.objects.count(), 1)
        self.assertEqual(Subscription.objects.count(), 1)

        # Second call (Duplicate)
        handle_stripe_webhook(json.dumps(payload), 'sig')
        self.assertEqual(StripeEvent.objects.count(), 1) # Should not create new event log
        self.assertEqual(Subscription.objects.count(), 1) # Should not create new subscription
