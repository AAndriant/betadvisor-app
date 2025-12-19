from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
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
