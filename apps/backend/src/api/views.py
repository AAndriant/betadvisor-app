from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend

from bets.models import BetTicket
from bets.serializers import BetTicketSerializer, BetCreateSerializer
from .serializers import UserProfileSerializer

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
        return BetTicketSerializer

    def perform_create(self, serializer):
        # On attache automatiquement l'auteur au ticket créé
        serializer.save(author=self.request.user)

class MyProfileView(APIView):
    """
    Endpoint Dashboard : Renvoie les infos du user connecté + ses stats calculées
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
