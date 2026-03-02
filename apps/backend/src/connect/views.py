from django.conf import settings
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

        # Use explicit settings-based URLs for return and refresh URLs, falling back to basic paths if needed
        return_url = getattr(settings, 'ONBOARDING_RETURN_URL', 'betadvisor://onboarding-return')
        refresh_url = getattr(settings, 'ONBOARDING_REFRESH_URL', 'betadvisor://onboarding-refresh')

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
