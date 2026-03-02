from django.urls import path
from connect.views import CreateConnectedAccountView, OnboardingLinkView, ConnectedAccountStatusView

app_name = 'connect'

urlpatterns = [
    path('create-account/', CreateConnectedAccountView.as_view(), name='create-account'),
    path('onboarding-link/', OnboardingLinkView.as_view(), name='onboarding-link'),
    path('status/', ConnectedAccountStatusView.as_view(), name='status'),
]
