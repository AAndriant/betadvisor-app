from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
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
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            send_mail(
                subject="BetAdvisor — Réinitialisation mot de passe",
                message=(
                    f"Bonjour {user.username},\n\n"
                    f"Voici vos informations pour réinitialiser votre mot de passe :\n\n"
                    f"  UID   : {uid}\n"
                    f"  Token : {token}\n\n"
                    f"Entrez ces informations dans l'application pour définir un nouveau mot de passe.\n\n"
                    f"Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.\n\n"
                    f"— BetAdvisor"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
            logger.info(f"Password reset email sent to {email}")
        except CustomUser.DoesNotExist:
            logger.info(f"Password reset requested for non-existent email: {email}")

        return Response({'status': 'If the email exists, a reset link has been sent.'})


class PasswordResetConfirmView(APIView):
    """
    POST /api/auth/password-reset/confirm/
    Accepts uid, token, new_password to complete password reset.
    """
    permission_classes = (AllowAny,)

    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not uid or not token or not new_password:
            return Response(
                {'error': 'uid, token, and new_password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = CustomUser.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            return Response(
                {'error': 'Invalid reset link'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response(
                {'error': list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()
        logger.info(f"Password reset completed for user {user.username}")

        return Response({'status': 'Password has been reset successfully.'})
