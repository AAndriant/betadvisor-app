from django.urls import path
from subscriptions.views import SubscribeView, CancelSubscriptionView

urlpatterns = [
    path('subscribe/', SubscribeView.as_view(), name='subscribe'),
    path('cancel/', CancelSubscriptionView.as_view(), name='cancel-subscription'),
]
