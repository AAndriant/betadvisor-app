from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache
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


class ThrottlingTests(APITestCase):
    def setUp(self):
        # Ensure cache is clear before testing throttles
        cache.clear()

    def test_login_throttling(self):
        """Test login endpoint is throttled after 5 requests per minute."""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }

        # First 5 requests should not be throttled (might be 401 Unauthorized, but not 429)
        for _ in range(5):
            response = self.client.post(url, data, format='json')
            self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # 6th request should be throttled
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_register_throttling(self):
        """Test register endpoint is throttled after 5 requests per minute."""
        url = reverse('users:register')
        data = {
            'username': 'testuser1',
            'email': 'testuser1@example.com',
            'password': 'StrongPassword123!'
        }

        # First 5 requests should not be throttled
        for i in range(5):
            # Change username/email slightly to avoid 400 Bad Request on duplicates
            req_data = data.copy()
            req_data['username'] = f"testuser{i}"
            req_data['email'] = f"testuser{i}@example.com"
            response = self.client.post(url, req_data, format='json')
            self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # 6th request should be throttled
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
