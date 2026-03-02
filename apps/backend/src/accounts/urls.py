from django.urls import path
from .views import RegisterView

urlpatterns = [
    path('api/auth/register/', RegisterView.as_view(), name='register'),
]
