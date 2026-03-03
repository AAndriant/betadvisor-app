from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

from bets.models import BetTicket
from bets.serializers import BetTicketSerializer, BetCreateSerializer, BetSettleSerializer
from .serializers import UserProfileSerializer

import logging

logger = logging.getLogger(__name__)


class BetViewSet(viewsets.ModelViewSet):
    """
    Gère l'affichage du Feed (List) et la création de tickets (Create)
    """
    queryset = BetTicket.objects.all().select_related('author').prefetch_related('likes', 'comments').order_by('-created_at')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = (MultiPartParser, FormParser) # Pour gérer l'upload d'image
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['author']

    def get_serializer_class(self):
        if self.action == 'create':
            return BetCreateSerializer
        if self.action == 'settle':
            return BetSettleSerializer
        return BetTicketSerializer

    def perform_create(self, serializer):
        # On attache automatiquement l'auteur au ticket créé
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def settle(self, request, pk=None):
        """Settle a bet (only by the author). POST /api/bets/{id}/settle/ {outcome: WON|LOST|VOID}"""
        bet = self.get_object()

        # Only the author can settle their own bet
        if bet.author != request.user:
            return Response(
                {'error': 'Only the bet author can settle this bet.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Only PENDING bets can be settled
        if bet.status != BetTicket.BetStatus.PENDING:
            return Response(
                {'error': f'Bet already settled as {bet.status}.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = BetSettleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        outcome = serializer.validated_data['outcome']
        bet.settle(outcome)

        # Update gamification stats
        _update_user_stats(bet.author, outcome)

        return Response(BetTicketSerializer(bet, context={'request': request}).data)


def _update_user_stats(user, outcome):
    """Update UserGlobalStats after a bet is settled."""
    try:
        from gamification.models import UserGlobalStats
        stats, _ = UserGlobalStats.objects.get_or_create(user=user)
        stats.total_bets += 1
        if outcome == 'WON':
            stats.wins += 1
            stats.current_streak += 1
            if stats.current_streak > stats.max_streak:
                stats.max_streak = stats.current_streak
        elif outcome == 'LOST':
            stats.losses += 1
            stats.current_streak = 0
        elif outcome == 'VOID':
            stats.voids += 1
        stats.save()
    except Exception as e:
        logger.error(f"Failed to update gamification stats: {e}")


class MyProfileView(APIView):
    """
    Endpoint Dashboard : Renvoie les infos du user connecté + ses stats calculées
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

