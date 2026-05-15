from rest_framework import viewsets, filters
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.response import Response
from api.serializers import UserProfileSerializer

User = get_user_model()

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour la Discovery : Recherche et Leaderboard des Tipsters.
    ReadOnly car les utilisateurs ne peuvent modifier que leur propre profil (via /api/me/).
    """
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['username']

    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        """
        Renvoie les utilisateurs triés par ROI (calculé via Python pour le MVP).
        
        Performance Note:
        - Pour la Bêta (<1000 users), ce tri Python est acceptable
        - En production, migrer vers des champs cached_roi dans le modèle User
        - Limite: Top 50 pour optimiser la response size
        
        Endpoint: GET /api/users/leaderboard/
        """
        # MVP-friendly cap: only users with bets can rank, and the candidate
        # pool stays bounded until ROI is cached in DB.
        users = (
            User.objects.filter(bets__isnull=False)
            .distinct()
            .select_related('global_stats', 'tipster_profile')
            .prefetch_related('followers')
            .order_by('-global_stats__reputation_score', 'username')[:500]
        )
        
        # Sérialise pour calculer les stats (ROI, win_rate, etc.)
        data = UserProfileSerializer(users, many=True).data
        
        # Tri en Python par ROI décroissant
        # Note: users sans bets auront ROI=0 et seront en fin de liste
        sorted_data = sorted(
            data, 
            key=lambda u: u['stats']['roi'] if u['stats'] else -999, 
            reverse=True
        )
        
        # Retourne uniquement le Top 50
        return Response(sorted_data[:50])
