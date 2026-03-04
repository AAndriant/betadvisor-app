from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()


def _create_test_image(size_kb=10, filename='test.jpg'):
    """Create a small test image."""
    img = Image.new('RGB', (100, 100), color='red')
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return SimpleUploadedFile(filename, buffer.read(), content_type='image/jpeg')


class ProfileUpdateTests(TestCase):
    """S8-01: Test profile update endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        """GET /api/me/ should return profile with avatar_url and bio."""
        response = self.client.get('/api/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('avatar_url', response.data)
        self.assertIn('bio', response.data)
        # Default avatar should be UI-Avatars fallback
        self.assertIn('ui-avatars.com', response.data['avatar_url'])

    def test_update_bio(self):
        """PUT /api/me/profile/ should update bio."""
        response = self.client.put('/api/me/profile/', {'bio': 'Hello World'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, 'Hello World')

    def test_update_bio_sanitization(self):
        """S8-06: Bio should be sanitized (HTML stripped)."""
        response = self.client.put(
            '/api/me/profile/',
            {'bio': '<script>alert("xss")</script>Hello'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertNotIn('<script>', self.user.bio)
        self.assertIn('Hello', self.user.bio)

    def test_update_avatar(self):
        """PUT /api/me/profile/ should accept avatar upload."""
        image = _create_test_image()
        response = self.client.put(
            '/api/me/profile/',
            {'avatar': image},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.avatar)

    def test_avatar_url_after_upload(self):
        """After avatar upload, avatar_url should NOT be ui-avatars fallback."""
        image = _create_test_image()
        self.client.put('/api/me/profile/', {'avatar': image}, format='multipart')
        self.user.refresh_from_db()
        self.assertNotIn('ui-avatars.com', self.user.avatar_url)


class PushTokenTests(TestCase):
    """S8-03: Test push token registration."""

    def setUp(self):
        self.user = User.objects.create_user(username='pushuser', password='testpass123')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_register_push_token(self):
        """POST /api/me/push-token/ should register a token."""
        response = self.client.post('/api/me/push-token/', {
            'token': 'ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]',
            'device_name': 'iPhone 15',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_invalid_push_token_format(self):
        """Should reject non-Expo push tokens."""
        response = self.client.post('/api/me/push-token/', {
            'token': 'invalid-token-format',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upsert_push_token(self):
        """Same token should be updated, not duplicated."""
        token_val = 'ExponentPushToken[aaabbbccc]'
        self.client.post('/api/me/push-token/', {'token': token_val, 'device_name': 'Old'})
        self.client.post('/api/me/push-token/', {'token': token_val, 'device_name': 'New'})
        from notifications.models import PushToken
        self.assertEqual(PushToken.objects.filter(token=token_val).count(), 1)
        self.assertEqual(PushToken.objects.get(token=token_val).device_name, 'New')


class InputValidationTests(TestCase):
    """S8-06: Test input validation hardening."""

    def setUp(self):
        self.user = User.objects.create_user(username='valuser', password='testpass123')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_match_title_xss_blocked(self):
        """match_title with script tags should be rejected or sanitized."""
        response = self.client.post('/api/bets/', {
            'match_title': '<script>alert("xss")</script>',
            'selection': 'Home Win',
            'odds': 2.50,
            'stake': 10.00,
        })
        # Should either 400 (invalid chars) or sanitize
        if response.status_code == status.HTTP_201_CREATED:
            from bets.models import BetTicket
            bet = BetTicket.objects.last()
            self.assertNotIn('<script>', bet.match_title)

    def test_match_title_valid(self):
        """Valid match title should pass validation."""
        response = self.client.post('/api/bets/', {
            'match_title': 'PSG vs Real Madrid',
            'selection': 'Home Win',
            'odds': 2.50,
            'stake': 10.00,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_comment_sanitization(self):
        """S8-06: Comments should have HTML stripped."""
        from bets.models import BetTicket
        from decimal import Decimal
        bet = BetTicket.objects.create(
            author=self.user,
            match_title='Test Match',
            selection='Home',
            odds=Decimal('2.00'),
            stake=Decimal('10.00'),
        )
        response = self.client.post('/api/social/comments/', {
            'content': '<b>Nice</b> <script>evil</script>bet!',
            'bet': str(bet.id),
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('<script>', response.data['content'])

    def test_stake_max_limit(self):
        """Stake above 1M should be rejected."""
        response = self.client.post('/api/bets/', {
            'match_title': 'Test Match',
            'selection': 'Home Win',
            'odds': 2.50,
            'stake': 2000000.00,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DynamicPricingTests(TestCase):
    """S8-05: Test dynamic Stripe pricing per tipster."""

    def setUp(self):
        self.tipster = User.objects.create_user(username='tipster', password='testpass123')
        from users.models import TipsterProfile
        self.profile = TipsterProfile.objects.create(
            user=self.tipster,
            subscription_price=19.99,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.tipster)

    def test_dashboard_shows_price(self):
        """GET /api/me/dashboard/ should return subscription_price."""
        response = self.client.get('/api/me/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['subscription_price'], '19.99')

    def test_update_price(self):
        """POST /api/me/dashboard/ should update subscription_price."""
        response = self.client.post('/api/me/dashboard/', {
            'subscription_price': '29.99'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        from decimal import Decimal
        self.assertEqual(self.profile.subscription_price, Decimal('29.99'))
        # stripe_price_id should be reset
        self.assertEqual(self.profile.stripe_price_id, '')

    def test_update_price_invalid(self):
        """Price below 1.00 should be rejected."""
        response = self.client.post('/api/me/dashboard/', {
            'subscription_price': '0.50'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profile_shows_subscription_price(self):
        """User profile should show subscription_price for tipsters."""
        response = self.client.get('/api/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['subscription_price'], '19.99')


class HealthCheckTests(TestCase):
    """S8-04: Test health check endpoint."""

    def test_health_endpoint(self):
        """GET /api/health/ should return 200 OK."""
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'status': 'ok'})
