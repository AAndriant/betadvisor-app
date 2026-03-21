from django.urls import path
from connect.views import (
    CreateConnectedAccountView,
    OnboardingLinkView,
    CreateCheckoutSessionDeprecatedView,
    BecomeTipsterView,
    TipsterStatusView,
)

app_name = 'connect'

urlpatterns = [
    path('create-account/', CreateConnectedAccountView.as_view(), name='create-account'),
    path('onboarding-link/', OnboardingLinkView.as_view(), name='onboarding-link'),
    path('create-checkout-session/', CreateCheckoutSessionDeprecatedView.as_view(), name='create-checkout-session'),
    path('become-tipster/', BecomeTipsterView.as_view(), name='become-tipster'),
    path('tipster-status/', TipsterStatusView.as_view(), name='tipster-status'),
]
