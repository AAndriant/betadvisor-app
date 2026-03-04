from django.contrib import admin
from .models import Like, Comment, Follow, Report

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

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'followed', 'created_at']
    list_filter = ['created_at']
    search_fields = ['follower__username', 'followed__username']
    raw_id_fields = ['follower', 'followed']

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'reason', 'status', 'target_preview', 'created_at']
    list_filter = ['reason', 'status', 'created_at']
    search_fields = ['reporter__username', 'details']
    readonly_fields = ['reporter', 'reported_user', 'reported_bet', 'reported_comment', 'reason', 'details', 'created_at']
    list_editable = ['status']
    date_hierarchy = 'created_at'
    list_per_page = 25

    def target_preview(self, obj):
        if obj.reported_user:
            return f"User: {obj.reported_user.username}"
        if obj.reported_bet:
            return f"Bet: {str(obj.reported_bet.id)[:8]}"
        if obj.reported_comment:
            return f"Comment: {obj.reported_comment.content[:30]}"
        return "—"
    target_preview.short_description = 'Target'
