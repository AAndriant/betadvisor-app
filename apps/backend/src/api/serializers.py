import re
import bleach
from rest_framework import serializers
from django.contrib.auth import get_user_model
from bets.models import BetTicket

User = get_user_model()

# ─────────────────────────────────────────────────────────────
# S8-06: Sanitization helpers
# ─────────────────────────────────────────────────────────────
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB

def sanitize_text(value):
    """Strip all HTML tags from text fields (anti-XSS)."""
    if value:
        return bleach.clean(value, tags=[], strip=True).strip()
    return value


def validate_image_size(image):
    """Reject images larger than 5 MB."""
    if image and hasattr(image, 'size') and image.size > MAX_IMAGE_SIZE:
        raise serializers.ValidationError(
            f"Image file too large. Max size is {MAX_IMAGE_SIZE // (1024 * 1024)}MB."
        )
    return image


class UserProfileSerializer(serializers.ModelSerializer):
    stats = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    bio = serializers.CharField(read_only=True, default='')
    follower_count = serializers.SerializerMethodField()
    is_followed_by_me = serializers.SerializerMethodField()
    subscription_price = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'bio', 'stats',
            'avatar_url', 'follower_count', 'is_followed_by_me',
            'is_tipster', 'subscription_price',
        ]

    def get_avatar_url(self, obj):
        return obj.avatar_url

    def get_subscription_price(self, obj):
        """Return tipster's subscription price if applicable."""
        if hasattr(obj, 'tipster_profile'):
            return str(obj.tipster_profile.subscription_price)
        return None

    def get_stats(self, obj):
        """Calcul dynamique des Unit Economics (ROI, Winrate)"""
        bets = BetTicket.objects.filter(author=obj).exclude(status='PENDING')
        total_bets = bets.count()

        if total_bets == 0:
            return {"roi": 0, "win_rate": 0, "total_bets": 0, "total_profit": 0}

        wins = bets.filter(status='WON').count()
        win_rate = (wins / total_bets) * 100

        total_stake = 0
        net_profit = 0

        for bet in bets:
            total_stake += bet.stake
            if bet.status == 'WON':
                gain = (bet.stake * bet.odds) - bet.stake
                net_profit += gain
            elif bet.status == 'LOST':
                net_profit -= bet.stake

        roi = (net_profit / total_stake * 100) if total_stake > 0 else 0

        return {
            "roi": round(roi, 2),
            "win_rate": round(win_rate, 1),
            "total_bets": total_bets,
            "total_profit": round(float(net_profit), 2)
        }

    def get_follower_count(self, obj):
        """Count of users following this profile"""
        return obj.followers.count()

    def get_is_followed_by_me(self, obj):
        """Check if the current user follows this profile"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from social.models import Follow
            return Follow.objects.filter(follower=request.user, followed=obj).exists()
        return False


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for PUT /api/me/profile/ — avatar + bio update."""

    class Meta:
        model = User
        fields = ['avatar', 'bio']

    def validate_bio(self, value):
        return sanitize_text(value)

    def validate_avatar(self, value):
        return validate_image_size(value)
