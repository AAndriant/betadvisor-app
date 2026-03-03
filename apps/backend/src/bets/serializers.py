from rest_framework import serializers
from django.apps import apps
from .models import BetTicket

class BetTicketSerializer(serializers.ModelSerializer):
    author_id = serializers.ReadOnlyField(source='author.id')
    author_name = serializers.ReadOnlyField(source='author.username')
    # On génère un avatar temporaire si l'utilisateur n'en a pas
    author_avatar = serializers.SerializerMethodField()
    
    # Social Metrics
    like_count = serializers.SerializerMethodField()
    is_liked_by_me = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    is_locked = serializers.SerializerMethodField()

    class Meta:
        model = BetTicket
        fields = [
            'id', 'author_id', 'author_name', 'author_avatar',
            'match_title', 'selection', 'odds', 'stake',
            'ticket_image', 'status', 'payout', 'settled_at',
            'created_at', 'is_premium', 'is_locked',
            'like_count', 'is_liked_by_me', 'comment_count'
        ]
        read_only_fields = ['id', 'status', 'payout', 'is_premium', 'author', 'created_at', 'settled_at']

    def get_is_locked(self, obj):
        # Default value, logic handled in to_representation
        return False

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")

        # Default to locked if premium and not authenticated
        is_locked = instance.is_premium

        if instance.is_premium and request and request.user.is_authenticated:
            # Author always sees their own bet
            if request.user == instance.author:
                is_locked = False
            else:
                Subscription = apps.get_model('subscriptions', 'Subscription')
                is_subscribed = Subscription.objects.filter(
                    follower=request.user,
                    tipster=instance.author,
                    status="active"
                ).exists()
                if is_subscribed:
                    is_locked = False

        if is_locked:
            data["odds"] = None
            data["stake"] = None
            data["payout"] = None
            data["is_locked"] = True
        else:
            data["is_locked"] = False

        return data

    def get_author_avatar(self, obj):
        # Fallback UI-Avatars en attendant le module User Profile complet
        return f"https://ui-avatars.com/api/?name={obj.author.username}&background=10b981&color=fff"
    
    def get_like_count(self, obj):
        """Total number of likes for this bet"""
        return obj.likes.count()
    
    def get_is_liked_by_me(self, obj):
        """Check if current user liked this bet"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
    
    def get_comment_count(self, obj):
        """Total number of comments for this bet"""
        return obj.comments.count()

class BetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BetTicket
        fields = ['match_title', 'selection', 'odds', 'stake', 'ticket_image', 'is_premium']

    def validate_stake(self, value):
        if value <= 0:
            raise serializers.ValidationError("La mise doit être positive.")
        return value

    def validate_odds(self, value):
        if value < 1.01:
            raise serializers.ValidationError("Les cotes doivent être d'au moins 1.01.")
        if value > 1000:
            raise serializers.ValidationError("Les cotes ne peuvent pas dépasser 1000.")
        return value


class BetSettleSerializer(serializers.Serializer):
    outcome = serializers.ChoiceField(choices=[
        ('WON', 'Won'),
        ('LOST', 'Lost'),
        ('VOID', 'Void'),
    ])
