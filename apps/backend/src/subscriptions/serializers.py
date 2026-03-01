from rest_framework import serializers
from subscriptions.models import Subscription

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['tipster', 'status', 'current_period_end']
        read_only_fields = ['tipster', 'status', 'current_period_end']
