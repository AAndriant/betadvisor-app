from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')

    def test_register_success(self):
        data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, 'testuser')
        self.assertNotIn('password', response.data)

    def test_register_password_mismatch(self):
        data = {
            'username': 'testuser2',
            'email': 'testuser2@example.com',
            'password': 'StrongPassword123!',
            'password_confirm': 'WrongPassword123!'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    def test_register_duplicate_email(self):
        User.objects.create_user(username='olduser', email='duplicate@example.com', password='Password123!')

        data = {
            'username': 'newuser',
            'email': 'duplicate@example.com',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('A user with that email already exists.', str(response.data))
        self.assertEqual(User.objects.count(), 1)
