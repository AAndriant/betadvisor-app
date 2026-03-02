from rest_framework import viewsets, filters, generics, status
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from api.serializers import UserProfileSerializer
from users.serializers import RegisterSerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """
    Endpoint for user registration.
    Requires no authentication.
    Returns generated SimpleJWT tokens upon successful registration.
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer
    throttle_classes = [AnonRateThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            },
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

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
        # Récupère tous les users (potentiellement limiter avec [:100] si DB trop large)
        users = User.objects.all()
        
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
