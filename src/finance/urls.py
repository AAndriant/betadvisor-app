from django.urls import path
from .views import StripeWebhookView, SuccessView, CancelView, ConnectRefreshView, ConnectReturnView

urlpatterns = [
    path('webhook/stripe/', StripeWebhookView.as_view(), name='stripe_webhook'),
    path('success/', SuccessView.as_view(), name='success'),
    path('cancel/', CancelView.as_view(), name='cancel'),
    path('connect/refresh/', ConnectRefreshView.as_view(), name='connect_refresh'),
    path('connect/return/', ConnectReturnView.as_view(), name='connect_return'),
]
