from django.contrib import admin
from .models import Like, Comment

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'bet', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'bet__id']
    readonly_fields = ['created_at']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'bet', 'content_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'bet__id', 'content']
    readonly_fields = ['created_at']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
