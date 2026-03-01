import logging
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from subscriptions.models import Subscription
from subscriptions.serializers import SubscriptionSerializer
from subscriptions.webhooks import process_stripe_webhook_payload, StripeWebhookSignatureError, StripeWebhookPayloadError

logger = logging.getLogger(__name__)

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
