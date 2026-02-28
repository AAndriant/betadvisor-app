from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Wallet, Transaction
from decimal import Decimal

User = get_user_model()

class WalletTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='financeuser', password='password')
        # Wallet is created via OneToOne if we implemented a signal?
        # But the provided code for finance/models.py did NOT include a signal.
        # So we must create it manually or expect it not to exist.
        # Existing signals.py was cleared.
        self.wallet = Wallet.objects.create(user=self.user)

    def test_wallet_balance(self):
        self.assertEqual(self.wallet.balance, Decimal("0.00"))

    def test_transaction_creation(self):
        tx = Transaction.objects.create(
            wallet=self.wallet,
            amount=Decimal("50.00"),
            transaction_type=Transaction.TransactionType.DEPOSIT
        )
        self.assertEqual(tx.amount, Decimal("50.00"))
        self.assertEqual(tx.transaction_type, "DEPOSIT")
