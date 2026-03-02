from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from connect.models import ConnectedAccount
from connect.services import create_express_account, create_onboarding_link, StripeConnectError
from connect.serializers import ConnectedAccountSerializer, OnboardingLinkSerializer

class CreateConnectedAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            account = create_express_account(request.user)
            serializer = ConnectedAccountSerializer(account)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except StripeConnectError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class OnboardingLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            account = request.user.connected_account
        except ConnectedAccount.DoesNotExist:
            return Response({'error': 'ConnectedAccount not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Accept return_url and refresh_url via GET parameters to support deep links (Expo)
        return_url = request.GET.get('return_url') or request.build_absolute_uri('/api/connect/return/')
        refresh_url = request.GET.get('refresh_url') or request.build_absolute_uri('/api/connect/refresh/')

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


class ConnectedAccountStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            account = request.user.connected_account
            return Response({
                'exists': True,
                'stripe_account_id': account.stripe_account_id,
                'charges_enabled': account.charges_enabled,
                'payouts_enabled': account.payouts_enabled,
                'onboarding_completed': account.onboarding_completed,
            }, status=status.HTTP_200_OK)
        except ConnectedAccount.DoesNotExist:
            return Response({
                'exists': False,
                'charges_enabled': False,
                'payouts_enabled': False,
                'onboarding_completed': False,
            }, status=status.HTTP_200_OK)
