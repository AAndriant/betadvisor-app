from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter
from api.views import BetViewSet, MyProfileView
from users.views import UserViewSet
from subscriptions.views import StripeWebhookView

# Router DRF standard
router = DefaultRouter()
router.register(r'bets', BetViewSet, basename='bet')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('admin/', admin.site.urls),
    # Routes API
    path('api/', include(router.urls)),
    path('api/me/', MyProfileView.as_view(), name='my-profile'),

    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/tickets/', include('tickets.urls')),
    path('api/social/', include('social.urls')),
    path('api/connect/', include('connect.urls')),
    path('api/stripe/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('finance/', include('finance.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
