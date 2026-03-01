from django.urls import path
from subscriptions.views import MySubscriptionsView

urlpatterns = [
    path('me/subscriptions/', MySubscriptionsView.as_view(), name='my-subscriptions'),
]
