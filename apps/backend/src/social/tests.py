from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from bets.models import BetTicket
from social.models import Comment

User = get_user_model()


class CommentPermissionTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='testpass123')
        self.other = User.objects.create_user(username='other', password='testpass123')
        self.bet = BetTicket.objects.create(
            author=self.owner,
            match_title='PSG vs OM',
            selection='PSG gagne',
            odds=Decimal('1.80'),
            stake=Decimal('10.00'),
        )
        self.comment = Comment.objects.create(
            user=self.owner,
            bet=self.bet,
            content='Owner comment',
        )

    def test_non_author_cannot_delete_comment(self):
        self.client.force_authenticate(user=self.other)

        response = self.client.delete(f'/api/social/comments/{self.comment.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Comment.objects.filter(id=self.comment.id).exists())

    def test_author_can_delete_comment(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.delete(f'/api/social/comments/{self.comment.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(id=self.comment.id).exists())
