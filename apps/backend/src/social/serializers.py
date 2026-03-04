from rest_framework import serializers
from .models import Comment, Like
from api.serializers import sanitize_text


class CommentSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.username')
    user_avatar = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'user_name', 'user_avatar', 'content', 'created_at', 'bet']
        read_only_fields = ['id', 'created_at', 'user_name', 'user_avatar']

    def get_user_avatar(self, obj):
        """Use real avatar_url property from CustomUser model."""
        return obj.user.avatar_url

    def validate_content(self, value):
        """S8-06: Sanitize comment content (anti-XSS)."""
        value = sanitize_text(value)
        if not value:
            raise serializers.ValidationError("Comment content cannot be empty.")
        if len(value) > 500:
            raise serializers.ValidationError("Comment must be 500 characters or fewer.")
        return value

    def create(self, validated_data):
        # Automatically set the user from the request
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'user', 'bet', 'created_at']
        read_only_fields = ['id', 'created_at', 'user']
