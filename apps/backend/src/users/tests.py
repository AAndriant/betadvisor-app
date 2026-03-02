from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import TipsterProfile

User = get_user_model()

class RegisterTests(APITestCase):
    url = reverse('users:register')

    def test_successful_registration(self):
        """Test user can register and receive tokens."""
        data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'StrongPassword123!'
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], data['username'])
        self.assertEqual(response.data['user']['email'], data['email'])

        user = User.objects.get(username=data['username'])
        self.assertTrue(user.check_password(data['password']))

        # Verify TipsterProfile was automatically created
        self.assertTrue(TipsterProfile.objects.filter(user=user).exists())

    def test_duplicate_email(self):
        """Test registration with existing email fails."""
        existing_user = User.objects.create_user(
            username='existinguser',
            email='testuser@example.com',
            password='Password123!'
        )

        data = {
            'username': 'newuser',
            'email': 'testuser@example.com',
            'password': 'StrongPassword123!'
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_weak_password(self):
        """Test registration with weak password fails."""
        data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': '123'  # Too short, should fail validate_password
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
