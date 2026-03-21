import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from connect.models import ConnectedAccount
from connect.services import create_express_account, create_onboarding_link, StripeConnectError
from connect.serializers import ConnectedAccountSerializer, OnboardingLinkSerializer
from users.models import TipsterProfile

logger = logging.getLogger(__name__)


class CreateConnectedAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            account = create_express_account(request.user)
            serializer = ConnectedAccountSerializer(account)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except StripeConnectError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CreateCheckoutSessionDeprecatedView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({'error': 'use /api/subscriptions/subscribe/'}, status=status.HTTP_410_GONE)

class OnboardingLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            account = request.user.connected_account
        except ConnectedAccount.DoesNotExist:
            return Response({'error': 'ConnectedAccount not found.'}, status=status.HTTP_404_NOT_FOUND)

        return_url = request.build_absolute_uri('/api/connect/return/')
        refresh_url = request.build_absolute_uri('/api/connect/refresh/')

        try:
            link = create_onboarding_link(
                stripe_account_id=account.stripe_account_id,
                return_url=return_url,
                refresh_url=refresh_url
            )
            serializer = OnboardingLinkSerializer({'url': link})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except StripeConnectError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BecomeTipsterView(APIView):
    """
    POST /api/connect/become-tipster/

    Self-service endpoint for users to become tipsters.
    Handles the full flow atomically:
    1. Creates TipsterProfile if it doesn't exist
    2. Creates Stripe Express ConnectedAccount if it doesn't exist
    3. Returns the Stripe onboarding link URL

    Optional body: { "subscription_price": "14.99" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # 1. Create TipsterProfile if not exists
        subscription_price = request.data.get('subscription_price', '9.99')
        try:
            subscription_price = float(subscription_price)
            if subscription_price < 1.0 or subscription_price > 9999.99:
                return Response(
                    {'error': 'Le prix doit être entre 1€ et 9999€'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'error': 'Format de prix invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )

        profile, profile_created = TipsterProfile.objects.get_or_create(
            user=user,
            defaults={'subscription_price': subscription_price}
        )
        if profile_created:
            logger.info(f"Created TipsterProfile for user {user.username} (price={subscription_price}€)")

        # 2. Create Stripe ConnectedAccount if not exists
        try:
            connected_account = user.connected_account
            logger.info(f"User {user.username} already has ConnectedAccount: {connected_account.stripe_account_id}")
        except ConnectedAccount.DoesNotExist:
            try:
                connected_account = create_express_account(user)
                logger.info(f"Created Stripe Express account for tipster {user.username}")
            except StripeConnectError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 3. If already fully onboarded, return success without a link
        if connected_account.onboarding_completed and connected_account.charges_enabled:
            return Response({
                'status': 'already_onboarded',
                'message': 'Vous êtes déjà opérationnel en tant que tipster !',
                'onboarding_completed': True,
                'charges_enabled': True,
            }, status=status.HTTP_200_OK)

        # 4. Generate onboarding link
        return_url = request.build_absolute_uri('/api/connect/return/')
        refresh_url = request.build_absolute_uri('/api/connect/refresh/')

        try:
            link = create_onboarding_link(
                stripe_account_id=connected_account.stripe_account_id,
                return_url=return_url,
                refresh_url=refresh_url,
            )
        except StripeConnectError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'onboarding_required',
            'onboarding_url': link,
            'onboarding_completed': False,
            'charges_enabled': connected_account.charges_enabled,
        }, status=status.HTTP_200_OK)


class TipsterStatusView(APIView):
    """
    GET /api/connect/tipster-status/

    Returns the current tipster/onboarding status for the authenticated user.
    Used by the mobile app to determine which CTA to show.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Check TipsterProfile
        is_tipster = hasattr(user, 'tipster_profile')

        # Check ConnectedAccount
        has_connected_account = False
        onboarding_completed = False
        charges_enabled = False

        try:
            ca = user.connected_account
            has_connected_account = True
            onboarding_completed = ca.onboarding_completed
            charges_enabled = ca.charges_enabled
        except ConnectedAccount.DoesNotExist:
            pass

        return Response({
            'is_tipster': is_tipster,
            'has_connected_account': has_connected_account,
            'onboarding_completed': onboarding_completed,
            'charges_enabled': charges_enabled,
            'subscription_price': str(user.tipster_profile.subscription_price) if is_tipster else None,
        })
