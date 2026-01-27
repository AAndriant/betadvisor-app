from rest_framework.views import APIView
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from users.permissions import IsTipster
from .models import Plan
from .serializers import PlanSerializer
from .services import create_stripe_product_and_price, create_checkout_session
from .webhooks import handle_stripe_webhook

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """
    API View to receive Stripe Webhooks.
    """
    permission_classes = [] # Allow any (Stripe verifies via signature)
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        if not sig_header:
            return Response({'error': 'Missing signature'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            handle_stripe_webhook(payload, sig_header)
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        except Exception as e:
            # Errors are logged in handle_stripe_webhook
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class SuccessView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({'status': 'Payment Successful'}, status=status.HTTP_200_OK)

class CancelView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({'status': 'Payment Cancelled'}, status=status.HTTP_200_OK)

class ConnectRefreshView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({'status': 'Connect Refresh'}, status=status.HTTP_200_OK)

class ConnectReturnView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({'status': 'Connect Return'}, status=status.HTTP_200_OK)


class PlanViewSet(viewsets.ModelViewSet):
    serializer_class = PlanSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsTipster]
        elif self.action == 'subscribe':
             permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        if self.action in ['list', 'retrieve', 'subscribe']:
            return Plan.objects.filter(is_active=True)
        return Plan.objects.filter(tipster=self.request.user)

    def perform_create(self, serializer):
        plan = serializer.save(tipster=self.request.user)
        create_stripe_product_and_price(plan)

    @action(detail=True, methods=['post'])
    def subscribe(self, request, pk=None):
        plan = self.get_object()
        try:
             checkout_url = create_checkout_session(request.user, plan)
             return Response({'checkout_url': checkout_url}, status=status.HTTP_200_OK)
        except Exception as e:
             return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
