from rest_framework import serializers
from subscriptions.models import Subscription

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['tipster', 'status', 'current_period_end']
        read_only_fields = ['tipster', 'status', 'current_period_end']


class TipsterDashboardSerializer(serializers.ModelSerializer):
    follower_username = serializers.CharField(source='follower.username', read_only=True)

    class Meta:
        model = Subscription
        fields = ['follower_username', 'status', 'created_at']
        read_only_fields = ['follower_username', 'status', 'created_at']
