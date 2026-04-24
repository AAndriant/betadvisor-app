import logging
from decimal import Decimal
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
from users.models import CustomUser, TipsterProfile
from subscriptions.models import Subscription
from subscriptions.serializers import SubscriptionSerializer, TipsterDashboardSerializer
from subscriptions.webhooks import process_stripe_webhook_payload, StripeWebhookSignatureError, StripeWebhookPayloadError
from subscriptions.services import create_subscription_checkout, TipsterNotOnboardedError

logger = logging.getLogger(__name__)

class SubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        tipster_id = request.data.get('tipster_id')

        if not tipster_id:
            return Response({'error': 'tipster_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        tipster = get_object_or_404(CustomUser, id=tipster_id)

        # Check for active subscription
        has_active_subscription = Subscription.objects.filter(
            follower=request.user,
            tipster=tipster,
            status='active'
        ).exists()

        if has_active_subscription:
            return Response({'error': 'Active subscription already exists'}, status=status.HTTP_409_CONFLICT)

        success_url = request.data.get('success_url', request.build_absolute_uri('/') + 'success/')
        cancel_url = request.data.get('cancel_url', request.build_absolute_uri('/') + 'cancel/')

        try:
            checkout_url = create_subscription_checkout(
                follower=request.user,
                tipster=tipster,
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


class CancelSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        subscription_id = request.data.get('subscription_id')
        if not subscription_id:
            return Response({'error': 'subscription_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            subscription = Subscription.objects.get(
                id=subscription_id,
                follower=request.user,
                status='active'
            )
        except Subscription.DoesNotExist:
            return Response({'error': 'Active subscription not found'}, status=status.HTTP_404_NOT_FOUND)

        from subscriptions.services import cancel_subscription
        try:
            cancel_subscription(subscription)
            return Response({'status': 'canceled'})
        except Exception as e:
            logger.error(f"Error canceling subscription: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TipsterDashboardView(APIView):
    """
    GET  /api/me/dashboard/ — Dashboard data for tipster
    POST /api/me/dashboard/ — Update subscription price (S8-05)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Single aggregate query instead of multiple filter().count() calls
        from django.db.models import Count, Q
        agg = Subscription.objects.filter(tipster=user).aggregate(
            active_count=Count('id', filter=Q(status='active')),
            total_count=Count('id'),
        )
        active_count = agg['active_count']
        total_count = agg['total_count']

        # S8-05: Use tipster's actual price
        price_per_month = Decimal('9.99')  # default
        try:
            profile = user.tipster_profile
            price_per_month = Decimal(str(profile.subscription_price))
        except TipsterProfile.DoesNotExist:
            pass

        PLATFORM_FEE = Decimal('0.20')
        revenue = Decimal(str(active_count)) * price_per_month * (Decimal('1') - PLATFORM_FEE)

        # Fetch recent active subscriptions for serialization (separate query, needed for serializer)
        recent_subs = Subscription.objects.filter(
            tipster=user, status='active'
        ).order_by('-created_at')[:10]

        data = {
            "active_subscribers": active_count,
            "total_subscribers_ever": total_count,
            "monthly_revenue_estimate": float(round(revenue, 2)),
            "subscription_price": f"{price_per_month:.2f}",
            "recent_subscriptions": TipsterDashboardSerializer(
                recent_subs, many=True
            ).data,
        }
        return Response(data)

    def post(self, request):
        """S8-05: Update subscription price for the tipster."""
        new_price = request.data.get('subscription_price')
        if new_price is None:
            return Response(
                {'error': 'subscription_price is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            new_price = Decimal(str(new_price))
        except Exception:
            return Response(
                {'error': 'Invalid price format'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_price < Decimal('1.00') or new_price > Decimal('9999.99'):
            return Response(
                {'error': 'Price must be between 1.00 and 9999.99 EUR'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            profile = request.user.tipster_profile
        except TipsterProfile.DoesNotExist:
            return Response(
                {'error': 'You must be a tipster to set a price'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Reset stripe_price_id so a new price is created on next checkout
        profile.subscription_price = new_price
        profile.stripe_price_id = ''
        profile.save(update_fields=['subscription_price', 'stripe_price_id'])

        logger.info(f"Tipster {request.user.username} updated price to {new_price} EUR/month")
        return Response({
            'subscription_price': str(new_price),
            'message': 'Price updated. New subscribers will be charged the new price.'
        })


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
