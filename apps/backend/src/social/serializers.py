from rest_framework import serializers
from .models import Comment, Like

class CommentSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.username')
    user_avatar = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'user_name', 'user_avatar', 'content', 'created_at', 'bet']
        read_only_fields = ['id', 'created_at', 'user_name', 'user_avatar']

    def get_user_avatar(self, obj):
        # Fallback UI-Avatars
        return f"https://ui-avatars.com/api/?name={obj.user.username}&background=10b981&color=fff"

    def create(self, validated_data):
        # Automatically set the user from the request
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'user', 'bet', 'created_at']
        read_only_fields = ['id', 'created_at', 'user']
