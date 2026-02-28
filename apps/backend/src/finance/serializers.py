from rest_framework import serializers
from .models import Wallet, Transaction

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['balance', 'currency', 'updated_at']
        read_only_fields = ['balance', 'currency', 'updated_at']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'transaction_type', 'reference_id', 'description', 'created_at']
        read_only_fields = ['id', 'amount', 'transaction_type', 'reference_id', 'description', 'created_at']
