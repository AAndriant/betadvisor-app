from rest_framework import serializers
from subscriptions.models import Subscription

class SubscriptionSerializer(serializers.ModelSerializer):
    tipster_username = serializers.CharField(source='tipster.username', read_only=True)

    class Meta:
        model = Subscription
        fields = ['id', 'tipster', 'tipster_username', 'status', 'current_period_end', 'created_at']
        read_only_fields = ['id', 'tipster', 'tipster_username', 'status', 'current_period_end', 'created_at']


class TipsterDashboardSerializer(serializers.ModelSerializer):
    follower_username = serializers.CharField(source='follower.username', read_only=True)

    class Meta:
        model = Subscription
        fields = ['follower_username', 'status', 'created_at']
        read_only_fields = ['follower_username', 'status', 'created_at']
