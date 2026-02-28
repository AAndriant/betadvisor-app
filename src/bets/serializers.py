from rest_framework import serializers
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

    class Meta:
        model = BetTicket
        fields = [
            'id', 'author_id', 'author_name', 'author_avatar',
            'match_title', 'selection', 'odds', 'stake',
            'ticket_image', 'status', 'payout',
            'created_at', 'is_premium',
            'like_count', 'is_liked_by_me', 'comment_count'
        ]
        read_only_fields = ['id', 'status', 'payout', 'is_premium', 'author', 'created_at']

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
        fields = ['match_title', 'selection', 'odds', 'stake', 'ticket_image']

    def validate_stake(self, value):
        if value <= 0:
            raise serializers.ValidationError("La mise doit être positive.")
        return value

