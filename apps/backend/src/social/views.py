from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Like, Comment, Follow
from .serializers import CommentSerializer, LikeSerializer
from bets.models import BetTicket

class LikeViewSet(viewsets.GenericViewSet):
    """
    ViewSet for handling Like toggle operations.
    Only provides the toggle action.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = LikeSerializer

    @action(detail=True, methods=['post'], url_path='toggle')
    def toggle(self, request, pk=None):
        """
        Toggle like on a bet. Creates if doesn't exist, deletes if exists.
        URL: POST /api/social/likes/{bet_id}/toggle/
        """
        bet = get_object_or_404(BetTicket, pk=pk)
        user = request.user

        like, created = Like.objects.get_or_create(user=user, bet=bet)
        
        if not created:
            # Like already existed, so delete it (unlike)
            like.delete()
            return Response({'liked': False}, status=status.HTTP_200_OK)
        else:
            # New like was created
            return Response({'liked': True}, status=status.HTTP_201_CREATED)

class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CRUD operations on Comments.
    List, Create, and Delete (owner only).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()

    def get_queryset(self):
        """
        Optionally filter comments by bet_id query parameter.
        """
        queryset = super().get_queryset()
        bet_id = self.request.query_params.get('bet_id')
        if bet_id:
            queryset = queryset.filter(bet_id=bet_id)
        return queryset

    def perform_create(self, serializer):
        """
        Automatically set the user from the request.
        """
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        """
        Only allow comment deletion by the author.
        """
        if instance.user != self.request.user:
            return Response(
                {'error': 'You can only delete your own comments'},
                status=status.HTTP_403_FORBIDDEN
            )
        instance.delete()

class FollowViewSet(viewsets.GenericViewSet):
    """
    ViewSet for handling Follow/Unfollow operations.
    Only provides the toggle action.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='toggle')
    def toggle(self, request, pk=None):
        """
        Toggle follow on a user. Creates if doesn't exist, deletes if exists.
        URL: POST /api/social/follow/{user_id}/toggle/
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        followed_user = get_object_or_404(User, pk=pk)
        follower = request.user

        # Prevent self-follow
        if follower == followed_user:
            return Response(
                {'error': 'You cannot follow yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )

        follow, created = Follow.objects.get_or_create(
            follower=follower,
            followed=followed_user
        )
        
        if not created:
            # Follow already existed, so delete it (unfollow)
            follow.delete()
            return Response({'followed': False}, status=status.HTTP_200_OK)
        else:
            # New follow was created
            return Response({'followed': True}, status=status.HTTP_201_CREATED)
