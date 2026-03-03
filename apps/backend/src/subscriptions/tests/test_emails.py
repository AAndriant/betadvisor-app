from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch

User = get_user_model()

class TestSubscriptionEmails(APITestCase):
    def setUp(self):
        self.tipster = User.objects.create_user(username="t", email="t@t.com", password="p")
        self.follower = User.objects.create_user(username="f", email="f@t.com", password="p")

    @patch("subscriptions.emails.send_mail")
    def test_new_subscriber_email_sent(self, mock_send):
        from subscriptions.emails import send_new_subscriber_email
        send_new_subscriber_email(self.tipster, self.follower)
        mock_send.assert_called_once()
        # Fallback handling for recipient_list depending on how it's passed (kwargs or args)
        if "recipient_list" in mock_send.call_args.kwargs:
            recipients = mock_send.call_args.kwargs["recipient_list"]
        else:
            recipients = mock_send.call_args.args[3]
        self.assertIn(self.tipster.email, recipients)

    @patch("subscriptions.emails.send_mail")
    def test_email_failure_does_not_crash(self, mock_send):
        mock_send.side_effect = Exception("SMTP error")
        from subscriptions.emails import send_new_subscriber_email
        # Should NOT raise — fail_silently + try/except
        send_new_subscriber_email(self.tipster, self.follower)

    @patch("subscriptions.emails.send_mail")
    def test_subscription_canceled_email_sent(self, mock_send):
        from subscriptions.emails import send_subscription_canceled_email
        send_subscription_canceled_email(self.tipster, self.follower)
        mock_send.assert_called_once()
        if "recipient_list" in mock_send.call_args.kwargs:
            recipients = mock_send.call_args.kwargs["recipient_list"]
        else:
            recipients = mock_send.call_args.args[3]
        self.assertIn(self.tipster.email, recipients)

    @patch("subscriptions.emails.send_mail")
    def test_welcome_subscriber_email_sent(self, mock_send):
        from subscriptions.emails import send_welcome_subscriber_email
        send_welcome_subscriber_email(self.follower, self.tipster)
        mock_send.assert_called_once()
        if "recipient_list" in mock_send.call_args.kwargs:
            recipients = mock_send.call_args.kwargs["recipient_list"]
        else:
            recipients = mock_send.call_args.args[3]
        self.assertIn(self.follower.email, recipients)
