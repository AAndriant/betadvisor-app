from rest_framework import serializers
from tickets.models import Ticket, BetSelection

class BetSelectionSerializer(serializers.ModelSerializer):
    match_name = serializers.SerializerMethodField()

    class Meta:
        model = BetSelection
        fields = ['id', 'match', 'match_name', 'selection', 'odds']

    def get_match_name(self, obj):
        return str(obj.match)

class TicketSerializer(serializers.ModelSerializer):
    bets = BetSelectionSerializer(source='selections', many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Ticket
        fields = ['id', 'image', 'status', 'status_display', 'ocr_raw_data', 'created', 'bets']
        read_only_fields = ['id', 'status', 'ocr_raw_data', 'created', 'bets']
