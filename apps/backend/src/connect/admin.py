from django.contrib import admin
from .models import ConnectedAccount

@admin.register(ConnectedAccount)
class ConnectedAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'stripe_account_id', 'charges_enabled', 'payouts_enabled', 'onboarding_completed', 'created')
    list_filter = ('charges_enabled', 'payouts_enabled', 'onboarding_completed')
    search_fields = ('user__username', 'stripe_account_id')
