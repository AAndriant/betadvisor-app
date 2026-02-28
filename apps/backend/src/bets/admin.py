from django.contrib import admin
from .models import BetTicket

@admin.register(BetTicket)
class BetTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'match_title', 'selection', 'status', 'created_at')
    list_filter = ('status', 'is_verified', 'is_premium')
    search_fields = ('match_title', 'selection', 'author__username')
