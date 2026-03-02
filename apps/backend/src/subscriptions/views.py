import logging
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from users.models import CustomUser
from subscriptions.models import Subscription
from subscriptions.serializers import SubscriptionSerializer
from subscriptions.webhooks import process_stripe_webhook_payload, StripeWebhookSignatureError, StripeWebhookPayloadError
from subscriptions.services import create_subscription_checkout, TipsterNotOnboardedError

logger = logging.getLogger(__name__)

class SubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        tipster_id = request.data.get('tipster_id')
        price_id = request.data.get('price_id')

        if not tipster_id or not price_id:
            return Response({'error': 'tipster_id and price_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        tipster = get_object_or_404(CustomUser, id=tipster_id)

        # Check for active subscription
        has_active_subscription = Subscription.objects.filter(
            follower=request.user,
            tipster=tipster,
            status='active'
        ).exists()

        if has_active_subscription:
            return Response({'error': 'Active subscription already exists'}, status=status.HTTP_409_CONFLICT)

        # Let the frontend determine the success/cancel URLs, or fallback to defaults from settings
        success_url = request.data.get('success_url', getattr(settings, 'CHECKOUT_SUCCESS_URL', 'betadvisor://checkout/success'))
        cancel_url = request.data.get('cancel_url', getattr(settings, 'CHECKOUT_CANCEL_URL', 'betadvisor://checkout/cancel'))

        try:
            checkout_url = create_subscription_checkout(
                follower=request.user,
                tipster=tipster,
                price_id=price_id,
                success_url=success_url,
                cancel_url=cancel_url
            )
            return Response({'checkout_url': checkout_url}, status=status.HTTP_200_OK)
        except TipsterNotOnboardedError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating subscription checkout: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MySubscriptionsView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return Subscription.objects.filter(
            follower=self.request.user,
            status='active'
        )

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.headers.get('Stripe-Signature')

        if not sig_header:
            logger.error("Missing Stripe-Signature header")
            return HttpResponseBadRequest("Missing Stripe-Signature header")

        webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        if not webhook_secret:
            logger.error("Missing STRIPE_WEBHOOK_SECRET")
            return HttpResponseBadRequest("Webhook secret misconfigured")

        try:
            process_stripe_webhook_payload(payload, sig_header, webhook_secret)
        except StripeWebhookPayloadError as e:
            logger.error(f"Invalid payload: {str(e)}")
            return HttpResponseBadRequest("Invalid payload")
        except StripeWebhookSignatureError as e:
            logger.error(f"Invalid signature: {str(e)}")
            return HttpResponseBadRequest("Invalid signature")
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            return HttpResponseBadRequest(f"Error processing webhook: {str(e)}")

        return HttpResponse(status=200)
