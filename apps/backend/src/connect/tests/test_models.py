from django.test import TestCase
from django.contrib.auth import get_user_model
from connect.models import ConnectedAccount

User = get_user_model()

class ConnectedAccountModelTest(TestCase):
    def test_str_method(self):
        user = User.objects.create(username="testuser", email="test@example.com")
        account = ConnectedAccount.objects.create(
            user=user,
            stripe_account_id="acct_123456",
            charges_enabled=True,
            onboarding_completed=True
        )
        self.assertEqual(str(account), "testuser — acct_123456")
