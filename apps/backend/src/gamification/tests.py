from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from gamification.models import UserGlobalStats, UserSportStats
from gamification.badges import FireStreakBadge, ExpertBadge
from gamification.utils import update_reputation, get_halo_color

User = get_user_model()


# ─────────────────────────────────────────────────────────────
# Tests for FireStreakBadge.check_condition
# ─────────────────────────────────────────────────────────────
class FireStreakBadgeTests(TestCase):
    """Jules review: Missing tests for FireStreakBadge.check_condition."""

    def setUp(self):
        self.badge = FireStreakBadge()
        self.user = User.objects.create_user(username='streakuser', password='testpass123')
        self.global_stats = UserGlobalStats.objects.create(user=self.user)

    def test_streak_below_threshold_returns_false(self):
        """Streak of 6 should NOT trigger the badge."""
        self.global_stats.current_streak = 6
        self.global_stats.save()
        self.assertFalse(self.badge.check_condition(self.global_stats))

    def test_streak_at_threshold_returns_true(self):
        """Streak of exactly 7 SHOULD trigger the badge."""
        self.global_stats.current_streak = 7
        self.global_stats.save()
        self.assertTrue(self.badge.check_condition(self.global_stats))

    def test_streak_above_threshold_returns_true(self):
        """Streak of 10 SHOULD still trigger the badge."""
        self.global_stats.current_streak = 10
        self.global_stats.save()
        self.assertTrue(self.badge.check_condition(self.global_stats))

    def test_streak_zero_returns_false(self):
        """Zero streak should NOT trigger the badge."""
        self.global_stats.current_streak = 0
        self.global_stats.save()
        self.assertFalse(self.badge.check_condition(self.global_stats))

    def test_wrong_stats_type_returns_false(self):
        """Passing UserSportStats (wrong type) should return False."""
        from sports.models import Sport
        sport = Sport.objects.create(name='Football')
        sport_stats = UserSportStats.objects.create(
            user=self.user, sport=sport, current_streak=10
        )
        self.assertFalse(self.badge.check_condition(sport_stats))


# ─────────────────────────────────────────────────────────────
# Tests for ExpertBadge.check_condition (bonus coverage)
# ─────────────────────────────────────────────────────────────
class ExpertBadgeTests(TestCase):
    """Additional coverage: ExpertBadge checks on UserSportStats."""

    def setUp(self):
        self.badge = ExpertBadge()
        self.user = User.objects.create_user(username='expertuser', password='testpass123')

    def test_winrate_above_65_with_enough_bets(self):
        """Sport stats with >65% winrate and >=15 bets should trigger."""
        from sports.models import Sport
        sport = Sport.objects.create(name='Tennis')
        sport_stats = UserSportStats.objects.create(
            user=self.user, sport=sport, total_bets=20, wins=14, losses=6
        )
        # winrate = 14/20 * 100 = 70%
        self.assertTrue(self.badge.check_condition(sport_stats))

    def test_winrate_below_65_returns_false(self):
        """Sport stats with <=65% winrate should NOT trigger."""
        from sports.models import Sport
        sport = Sport.objects.create(name='Basketball')
        sport_stats = UserSportStats.objects.create(
            user=self.user, sport=sport, total_bets=20, wins=12, losses=8
        )
        # winrate = 12/20 * 100 = 60%
        self.assertFalse(self.badge.check_condition(sport_stats))

    def test_not_enough_bets_returns_false(self):
        """Even with high winrate, <15 bets should NOT trigger."""
        from sports.models import Sport
        sport = Sport.objects.create(name='MMA')
        sport_stats = UserSportStats.objects.create(
            user=self.user, sport=sport, total_bets=10, wins=9, losses=1
        )
        self.assertFalse(self.badge.check_condition(sport_stats))

    def test_global_stats_returns_false(self):
        """ExpertBadge requires UserSportStats, not UserGlobalStats."""
        global_stats = UserGlobalStats.objects.create(user=self.user, total_bets=20, wins=18)
        self.assertFalse(self.badge.check_condition(global_stats))


# ─────────────────────────────────────────────────────────────
# Tests for update_reputation
# ─────────────────────────────────────────────────────────────
class UpdateReputationTests(TestCase):
    """Jules review: Missing tests for update_reputation function."""

    def setUp(self):
        self.user = User.objects.create_user(username='repuser', password='testpass123')
        self.global_stats = UserGlobalStats.objects.create(user=self.user)

    @patch('gamification.utils.calculate_reputation_score')
    def test_high_score_sets_gold_halo(self, mock_calc):
        """Score >= 80 should set gold halo."""
        mock_calc.return_value = 85
        update_reputation(self.user)
        self.global_stats.refresh_from_db()
        self.assertEqual(self.global_stats.reputation_score, 85)
        self.assertEqual(self.global_stats.profile_halo_color, 'gold')

    @patch('gamification.utils.calculate_reputation_score')
    def test_medium_score_sets_silver_halo(self, mock_calc):
        """Score >= 60 and < 80 should set silver halo."""
        mock_calc.return_value = 70
        update_reputation(self.user)
        self.global_stats.refresh_from_db()
        self.assertEqual(self.global_stats.reputation_score, 70)
        self.assertEqual(self.global_stats.profile_halo_color, 'silver')

    @patch('gamification.utils.calculate_reputation_score')
    def test_low_score_sets_bronze_halo(self, mock_calc):
        """Score >= 40 and < 60 should set bronze halo."""
        mock_calc.return_value = 45
        update_reputation(self.user)
        self.global_stats.refresh_from_db()
        self.assertEqual(self.global_stats.reputation_score, 45)
        self.assertEqual(self.global_stats.profile_halo_color, 'bronze')

    @patch('gamification.utils.calculate_reputation_score')
    def test_zero_score_sets_none_halo(self, mock_calc):
        """Score < 40 should set none halo."""
        mock_calc.return_value = 0
        update_reputation(self.user)
        self.global_stats.refresh_from_db()
        self.assertEqual(self.global_stats.reputation_score, 0)
        self.assertEqual(self.global_stats.profile_halo_color, 'none')

    @patch('gamification.utils.calculate_reputation_score')
    def test_boundary_score_80_is_gold(self, mock_calc):
        """Score exactly 80 should be gold."""
        mock_calc.return_value = 80
        update_reputation(self.user)
        self.global_stats.refresh_from_db()
        self.assertEqual(self.global_stats.profile_halo_color, 'gold')

    @patch('gamification.utils.calculate_reputation_score')
    def test_boundary_score_60_is_silver(self, mock_calc):
        """Score exactly 60 should be silver."""
        mock_calc.return_value = 60
        update_reputation(self.user)
        self.global_stats.refresh_from_db()
        self.assertEqual(self.global_stats.profile_halo_color, 'silver')

    @patch('gamification.utils.calculate_reputation_score')
    def test_boundary_score_40_is_bronze(self, mock_calc):
        """Score exactly 40 should be bronze."""
        mock_calc.return_value = 40
        update_reputation(self.user)
        self.global_stats.refresh_from_db()
        self.assertEqual(self.global_stats.profile_halo_color, 'bronze')


# ─────────────────────────────────────────────────────────────
# Tests for get_halo_color utility
# ─────────────────────────────────────────────────────────────
class GetHaloColorTests(TestCase):
    """Unit tests for the get_halo_color helper."""

    def test_gold(self):
        self.assertEqual(get_halo_color(80), 'gold')
        self.assertEqual(get_halo_color(100), 'gold')

    def test_silver(self):
        self.assertEqual(get_halo_color(60), 'silver')
        self.assertEqual(get_halo_color(79), 'silver')

    def test_bronze(self):
        self.assertEqual(get_halo_color(40), 'bronze')
        self.assertEqual(get_halo_color(59), 'bronze')

    def test_none(self):
        self.assertEqual(get_halo_color(0), 'none')
        self.assertEqual(get_halo_color(39), 'none')
