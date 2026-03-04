from rest_framework import serializers
from .models import PushToken, Notification


class PushTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushToken
        fields = ['id', 'token', 'device_name']
        read_only_fields = ['id']
        extra_kwargs = {
            'token': {'validators': []},  # We handle uniqueness via upsert in create()
        }

    def validate_token(self, value):
        """Validate Expo push token format."""
        if not value.startswith('ExponentPushToken[') and not value.startswith('ExpoPushToken['):
            raise serializers.ValidationError(
                "Invalid push token format. Must be an Expo push token."
            )
        return value

    def create(self, validated_data):
        """Create or update push token — upsert by token value."""
        user = self.context['request'].user
        token, created = PushToken.objects.update_or_create(
            token=validated_data['token'],
            defaults={
                'user': user,
                'device_name': validated_data.get('device_name', ''),
                'is_active': True,
            }
        )
        return token


class NotificationSerializer(serializers.ModelSerializer):
    sender_username = serializers.ReadOnlyField(source='sender.username')
    sender_avatar = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'body',
            'data', 'is_read', 'sender_username', 'sender_avatar',
            'created',
        ]
        read_only_fields = ['id', 'notification_type', 'title', 'body', 'data', 'created']

    def get_sender_avatar(self, obj):
        if obj.sender:
            return obj.sender.avatar_url
        return None
