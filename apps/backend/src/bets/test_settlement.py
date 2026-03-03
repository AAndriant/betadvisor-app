"""Tests for the auto-settlement system."""
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from bets.models import BetTicket
from bets.prediction_models import Prediction
from bets.sports_api import verify_prediction, extract_score, is_match_finished
from users.models import CustomUser


class PredictionModelTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='tipster', email='t@test.com', password='p'
        )
        self.ticket = BetTicket.objects.create(
            author=self.user,
            match_title='PSG vs Real Madrid',
            selection='Home Win',
            odds=Decimal('2.50'),
            stake=Decimal('10.00'),
        )

    def test_create_prediction(self):
        pred = Prediction.objects.create(
            bet_ticket=self.ticket,
            match_title='PSG vs Real Madrid',
            sport='FOOTBALL',
            prediction_type='MATCH_RESULT',
            prediction_value='Home Win',
        )
        self.assertEqual(pred.outcome, 'PENDING')
        self.assertIsNone(pred.resolved_at)

    def test_resolve_prediction(self):
        pred = Prediction.objects.create(
            bet_ticket=self.ticket,
            match_title='PSG vs Real Madrid',
            sport='FOOTBALL',
            prediction_type='MATCH_RESULT',
            prediction_value='Home Win',
        )
        pred.resolve('CORRECT', {'score': {'home': 2, 'away': 1}})
        pred.refresh_from_db()
        self.assertEqual(pred.outcome, 'CORRECT')
        self.assertIsNotNone(pred.resolved_at)
        self.assertEqual(pred.actual_result['score']['home'], 2)


class VerifyPredictionTests(TestCase):
    """Test the pure verification logic."""

    # ── Match Result (1N2) ──
    def test_match_result_home_win_correct(self):
        result = verify_prediction('MATCH_RESULT', 'Home Win', {'home': 3, 'away': 1})
        self.assertEqual(result, 'CORRECT')

    def test_match_result_home_win_incorrect(self):
        result = verify_prediction('MATCH_RESULT', 'Home Win', {'home': 0, 'away': 2})
        self.assertEqual(result, 'INCORRECT')

    def test_match_result_draw_correct(self):
        result = verify_prediction('MATCH_RESULT', 'Draw', {'home': 1, 'away': 1})
        self.assertEqual(result, 'CORRECT')

    def test_match_result_draw_incorrect(self):
        result = verify_prediction('MATCH_RESULT', 'Draw', {'home': 2, 'away': 1})
        self.assertEqual(result, 'INCORRECT')

    def test_match_result_away_win_correct(self):
        result = verify_prediction('MATCH_RESULT', '2', {'home': 0, 'away': 1})
        self.assertEqual(result, 'CORRECT')

    def test_match_result_codes(self):
        """Test using numeric codes 1, N, 2."""
        self.assertEqual(
            verify_prediction('MATCH_RESULT', '1', {'home': 2, 'away': 0}), 'CORRECT'
        )
        self.assertEqual(
            verify_prediction('MATCH_RESULT', 'N', {'home': 1, 'away': 1}), 'CORRECT'
        )

    # ── Over/Under ──
    def test_over_correct(self):
        result = verify_prediction('OVER_UNDER', 'Over 2.5', {'home': 2, 'away': 1})
        self.assertEqual(result, 'CORRECT')

    def test_over_incorrect(self):
        result = verify_prediction('OVER_UNDER', 'Over 2.5', {'home': 1, 'away': 0})
        self.assertEqual(result, 'INCORRECT')

    def test_under_correct(self):
        result = verify_prediction('OVER_UNDER', 'Under 3.5', {'home': 1, 'away': 1})
        self.assertEqual(result, 'CORRECT')

    # ── BTTS ──
    def test_btts_yes_correct(self):
        result = verify_prediction('BTTS', 'Yes', {'home': 1, 'away': 2})
        self.assertEqual(result, 'CORRECT')

    def test_btts_yes_incorrect(self):
        result = verify_prediction('BTTS', 'Yes', {'home': 2, 'away': 0})
        self.assertEqual(result, 'INCORRECT')

    def test_btts_no_correct(self):
        result = verify_prediction('BTTS', 'No', {'home': 3, 'away': 0})
        self.assertEqual(result, 'CORRECT')

    # ── Double Chance ──
    def test_double_chance_1x_correct_home(self):
        result = verify_prediction('DOUBLE_CHANCE', '1X', {'home': 2, 'away': 0})
        self.assertEqual(result, 'CORRECT')

    def test_double_chance_1x_correct_draw(self):
        result = verify_prediction('DOUBLE_CHANCE', '1X', {'home': 1, 'away': 1})
        self.assertEqual(result, 'CORRECT')

    def test_double_chance_1x_incorrect(self):
        result = verify_prediction('DOUBLE_CHANCE', '1X', {'home': 0, 'away': 2})
        self.assertEqual(result, 'INCORRECT')

    # ── Correct Score ──
    def test_correct_score_correct(self):
        result = verify_prediction('CORRECT_SCORE', '2-1', {'home': 2, 'away': 1})
        self.assertEqual(result, 'CORRECT')

    def test_correct_score_incorrect(self):
        result = verify_prediction('CORRECT_SCORE', '2-1', {'home': 1, 'away': 1})
        self.assertEqual(result, 'INCORRECT')

    # ── Goalscorer ──
    def test_goalscorer_correct(self):
        events = [
            {'type': 'Goal', 'player': {'name': 'Kylian Mbappé'}},
            {'type': 'Goal', 'player': {'name': 'Vinicius Jr'}},
        ]
        result = verify_prediction('GOALSCORER', 'Mbappé', {'home': 2, 'away': 0}, events)
        self.assertEqual(result, 'CORRECT')

    def test_goalscorer_incorrect(self):
        events = [
            {'type': 'Goal', 'player': {'name': 'Vinicius Jr'}},
        ]
        result = verify_prediction('GOALSCORER', 'Mbappé', {'home': 0, 'away': 1}, events)
        self.assertEqual(result, 'INCORRECT')

    def test_goalscorer_no_events(self):
        result = verify_prediction('GOALSCORER', 'Mbappé', {'home': 2, 'away': 0})
        self.assertEqual(result, 'UNVERIFIABLE')

    # ── Edge Cases ──
    def test_missing_score(self):
        result = verify_prediction('MATCH_RESULT', 'Home Win', {'home': None, 'away': None})
        self.assertEqual(result, 'UNVERIFIABLE')


class IsMatchFinishedTests(TestCase):
    def test_football_finished(self):
        fixture = {'fixture': {'status': {'short': 'FT'}}}
        self.assertTrue(is_match_finished(fixture, 'FOOTBALL'))

    def test_football_not_finished(self):
        fixture = {'fixture': {'status': {'short': '2H'}}}
        self.assertFalse(is_match_finished(fixture, 'FOOTBALL'))

    def test_football_extra_time(self):
        fixture = {'fixture': {'status': {'short': 'AET'}}}
        self.assertTrue(is_match_finished(fixture, 'FOOTBALL'))


class ExtractScoreTests(TestCase):
    def test_football_score(self):
        fixture = {'goals': {'home': 3, 'away': 1}}
        score = extract_score(fixture, 'FOOTBALL')
        self.assertEqual(score, {'home': 3, 'away': 1})

    def test_basketball_score(self):
        fixture = {'scores': {'home': {'total': 110}, 'away': {'total': 105}}}
        score = extract_score(fixture, 'BASKETBALL')
        self.assertEqual(score, {'home': 110, 'away': 105})
