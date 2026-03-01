from rest_framework import serializers
from connect.models import ConnectedAccount

class ConnectedAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnectedAccount
        fields = ['stripe_account_id', 'onboarding_completed']
        read_only_fields = ['stripe_account_id', 'onboarding_completed']

class OnboardingLinkSerializer(serializers.Serializer):
    url = serializers.URLField()
