from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class ConnectDeprecatedRouteTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='password123'
        )
        self.url = reverse('connect:create-checkout-session')

    def test_create_checkout_session_deprecated(self):
        """Test POST /api/connect/create-checkout-session/ returns 410 Gone."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        self.assertEqual(response.data, {'error': 'use /api/subscriptions/subscribe/'})
