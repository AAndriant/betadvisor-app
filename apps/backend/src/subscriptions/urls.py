from django.urls import path
from subscriptions.views import SubscribeView

urlpatterns = [
    path('subscribe/', SubscribeView.as_view(), name='subscribe'),
]
