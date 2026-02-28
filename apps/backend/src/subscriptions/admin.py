from django.contrib import admin
from .models import Subscription, StripeEvent

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('follower', 'tipster', 'status', 'current_period_end', 'stripe_subscription_id')
    list_filter = ('status', 'current_period_end')
    search_fields = ('follower__username', 'tipster__username', 'stripe_subscription_id', 'stripe_customer_id')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(StripeEvent)
class StripeEventAdmin(admin.ModelAdmin):
    list_display = ('stripe_event_id', 'event_type', 'processed_at')
    list_filter = ('event_type', 'processed_at')
    search_fields = ('stripe_event_id', 'event_type')
    readonly_fields = ('stripe_event_id', 'event_type', 'processed_at', 'payload')
