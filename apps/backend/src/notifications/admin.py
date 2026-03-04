from django.contrib import admin
from .models import PushToken, Notification


@admin.register(PushToken)
class PushTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'device_name', 'is_active', 'created')
    list_filter = ('is_active',)
    search_fields = ('user__username', 'token')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'title', 'is_read', 'push_sent', 'created')
    list_filter = ('notification_type', 'is_read', 'push_sent')
    search_fields = ('recipient__username', 'title')
