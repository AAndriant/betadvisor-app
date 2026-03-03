from django.urls import path
from .views import RegisterView, PasswordResetRequestView

urlpatterns = [
    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/auth/password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
]
