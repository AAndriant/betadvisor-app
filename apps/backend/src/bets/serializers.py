import re
import bleach
from rest_framework import serializers
from django.apps import apps
from .models import BetTicket
from api.serializers import sanitize_text, validate_image_size


class BetTicketSerializer(serializers.ModelSerializer):
    author_id = serializers.ReadOnlyField(source='author.id')
    author_name = serializers.ReadOnlyField(source='author.username')
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
        return False

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")

        is_locked = instance.is_premium

        if instance.is_premium and request and request.user.is_authenticated:
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
        """Use real avatar_url property from CustomUser model."""
        return obj.author.avatar_url

    def get_like_count(self, obj):
        return obj.likes.count()

    def get_is_liked_by_me(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_comment_count(self, obj):
        return obj.comments.count()


class BetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BetTicket
        fields = ['match_title', 'selection', 'odds', 'stake', 'ticket_image', 'is_premium']

    # ─── S8-06: Input validation hardening ───────────────────
    def validate_match_title(self, value):
        """Validate match_title: max length, allowed characters (anti-XSS)."""
        value = sanitize_text(value)
        if len(value) > 255:
            raise serializers.ValidationError("Match title must be 255 characters or fewer.")
        # Allow letters, numbers, spaces, hyphens, periods, parentheses, vs/VS
        if not re.match(r'^[\w\s\-\.()\/\':,&àâäéèêëïîôùûüçÀÂÄÉÈÊËÏÎÔÙÛÜÇ]+$', value, re.UNICODE):
            raise serializers.ValidationError(
                "Match title contains invalid characters."
            )
        return value

    def validate_selection(self, value):
        """Sanitize selection field."""
        return sanitize_text(value)

    def validate_stake(self, value):
        if value <= 0:
            raise serializers.ValidationError("La mise doit être positive.")
        if value > 1000000:
            raise serializers.ValidationError("La mise ne peut pas dépasser 1 000 000.")
        return value

    def validate_odds(self, value):
        if value < 1.01:
            raise serializers.ValidationError("Les cotes doivent être d'au moins 1.01.")
        if value > 1000:
            raise serializers.ValidationError("Les cotes ne peuvent pas dépasser 1000.")
        return value

    def validate_ticket_image(self, value):
        """S8-06: Limit image size to 5 MB."""
        return validate_image_size(value)


class BetSettleSerializer(serializers.Serializer):
    outcome = serializers.ChoiceField(choices=[
        ('WON', 'Won'),
        ('LOST', 'Lost'),
        ('VOID', 'Void'),
    ])
