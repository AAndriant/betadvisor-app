from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Like, Comment
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
