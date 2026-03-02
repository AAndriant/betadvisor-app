from django.urls import path
from connect.views import CreateConnectedAccountView, OnboardingLinkView

app_name = 'connect'

from subscriptions.views import SubscribeView

urlpatterns = [
    path('create-account/', CreateConnectedAccountView.as_view(), name='create-account'),
    path('onboarding-link/', OnboardingLinkView.as_view(), name='onboarding-link'),
    path('create-checkout-session/', SubscribeView.as_view(), name='create-checkout-session'),
]
