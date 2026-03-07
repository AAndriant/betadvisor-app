import bleach
from decimal import Decimal
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Case, When, F, Q, DecimalField, Value
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
    sport_stats = serializers.SerializerMethodField()
    badges = serializers.SerializerMethodField()
    halo_color = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'bio', 'stats',
            'avatar_url', 'follower_count', 'is_followed_by_me',
            'is_tipster', 'subscription_price', 'sport_stats',
            'badges', 'halo_color',
        ]

    def get_avatar_url(self, obj):
        return obj.avatar_url

    def get_subscription_price(self, obj):
        """Return tipster's subscription price if applicable."""
        if hasattr(obj, 'tipster_profile'):
            return str(obj.tipster_profile.subscription_price)
        return None

    def get_stats(self, obj):
        """Calcul dynamique des Unit Economics (ROI, Winrate) via DB aggregations."""
        agg = BetTicket.objects.filter(author=obj).exclude(status='PENDING').aggregate(
            total_bets=Count('id'),
            wins=Count('id', filter=Q(status='WON')),
            total_stake=Sum('stake'),
            won_revenue=Sum(
                Case(
                    When(status='WON', then=F('stake') * F('odds') - F('stake')),
                    default=Value(Decimal('0.00')),
                    output_field=DecimalField(),
                )
            ),
            lost_stakes=Sum(
                Case(
                    When(status='LOST', then=F('stake')),
                    default=Value(Decimal('0.00')),
                    output_field=DecimalField(),
                )
            ),
        )

        total_bets = agg['total_bets'] or 0
        if total_bets == 0:
            return {"roi": 0, "win_rate": 0, "total_bets": 0, "total_profit": 0}

        wins = agg['wins'] or 0
        win_rate = (wins / total_bets) * 100

        won_revenue = agg['won_revenue'] or Decimal('0.00')
        lost_stakes = agg['lost_stakes'] or Decimal('0.00')
        net_profit = won_revenue - lost_stakes
        total_stake = agg['total_stake'] or Decimal('0.00')

        roi = (float(net_profit) / float(total_stake) * 100) if total_stake > 0 else 0

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

    def get_sport_stats(self, obj):
        try:
            from gamification.models import UserSportStats
            stats = UserSportStats.objects.filter(user=obj).select_related('sport')
            return [{
                'sport': s.sport.name,
                'total_bets': s.total_bets,
                'wins': s.wins,
                'winrate': round(s.winrate, 1),
                'roi': round(float(s.roi), 1),
            } for s in stats]
        except Exception:
            return []

    def get_badges(self, obj):
        try:
            from gamification.models import UserBadge
            badges = UserBadge.objects.filter(user=obj).only(
                'badge_name', 'description', 'awarded_at'
            ).order_by('-awarded_at')
            return [{
                'badge_name': b.badge_name,
                'description': b.description,
                'awarded_at': b.awarded_at.isoformat() if b.awarded_at else None,
            } for b in badges]
        except Exception:
            return []

    def get_halo_color(self, obj):
        try:
            return obj.global_stats.profile_halo_color
        except Exception:
            return 'none'


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for PUT /api/me/profile/ — avatar + bio update."""

    class Meta:
        model = User
        fields = ['avatar', 'bio']

    def validate_bio(self, value):
        return sanitize_text(value)

    def validate_avatar(self, value):
        return validate_image_size(value)
