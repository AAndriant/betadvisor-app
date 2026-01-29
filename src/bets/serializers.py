from rest_framework import serializers
from .models import BetTicket

class BetTicketSerializer(serializers.ModelSerializer):
    author_name = serializers.ReadOnlyField(source='author.username')
    # On génère un avatar temporaire si l'utilisateur n'en a pas
    author_avatar = serializers.SerializerMethodField()

    class Meta:
        model = BetTicket
        fields = [
            'id', 'author_name', 'author_avatar',
            'match_title', 'selection', 'odds', 'stake',
            'ticket_image', 'status', 'payout',
            'created_at', 'is_premium'
        ]
        read_only_fields = ['id', 'status', 'payout', 'is_premium', 'author', 'created_at']

    def get_author_avatar(self, obj):
        # Fallback UI-Avatars en attendant le module User Profile complet
        return f"https://ui-avatars.com/api/?name={obj.author.username}&background=10b981&color=fff"

class BetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BetTicket
        fields = ['match_title', 'selection', 'odds', 'stake', 'ticket_image']

    def validate_stake(self, value):
        if value <= 0:
            raise serializers.ValidationError("La mise doit être positive.")
        return value
