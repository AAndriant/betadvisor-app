from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from .serializers import RegisterSerializer
from users.models import CustomUser
import logging

logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


class PasswordResetRequestView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'email is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Always return 200 to prevent email enumeration
        try:
            user = CustomUser.objects.get(email=email)
            token = default_token_generator.make_token(user)
            # In production, this would send a link to a password reset page
            send_mail(
                subject="BetAdvisor — Password Reset",
                message=f"Your password reset token is: {token}\n\nUse this token to reset your password.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
            logger.info(f"Password reset email sent to {email}")
        except CustomUser.DoesNotExist:
            logger.info(f"Password reset requested for non-existent email: {email}")

        return Response({'status': 'If the email exists, a reset link has been sent.'})
