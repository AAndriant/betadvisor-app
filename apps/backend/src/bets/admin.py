from django.contrib import admin
from .models import BetTicket
from .prediction_models import Prediction

@admin.register(BetTicket)
class BetTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'match_title', 'selection', 'odds', 'status', 'is_premium', 'created_at')
    list_filter = ('status', 'is_verified', 'is_premium', 'created_at')
    search_fields = ('match_title', 'selection', 'author__username')
    readonly_fields = ('id', 'payout', 'settled_at', 'created_at', 'updated_at')
    raw_id_fields = ('author',)
    date_hierarchy = 'created_at'
    list_per_page = 25

@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ('match_title', 'sport', 'prediction_type', 'prediction_value', 'outcome', 'api_fixture_id', 'resolved_at')
    list_filter = ('sport', 'prediction_type', 'outcome')
    search_fields = ('match_title', 'prediction_value')
    readonly_fields = ('resolved_at', 'actual_result', 'created', 'modified')
    raw_id_fields = ('bet_ticket',)
    date_hierarchy = 'created'
