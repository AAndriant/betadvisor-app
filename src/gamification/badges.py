from abc import ABC, abstractmethod
from decimal import Decimal
from django.utils import timezone
from django.db.models import F
from datetime import timedelta
from gamification.models import UserBadge, UserSportStats, UserGlobalStats
from tickets.models import BetSelection

class BaseBadge(ABC):
    slug = None
    name = None
    description = None

    @abstractmethod
    def check_condition(self, stats, bet_selection):
        """
        Check if the user meets the condition for this badge.
        :param stats: The UserGlobalStats or UserSportStats object (depending on context, usually Global or passed explicitly)
        :param bet_selection: The BetSelection that triggered the check (optional, useful for context)
        :return: Boolean
        """
        pass

    def award(self, user):
        UserBadge.objects.get_or_create(
            user=user,
            badge_name=self.slug,
            defaults={'description': self.description}
        )

# Original Badge: Sniper (Keep or Remove? The prompt replaced them with "Expert", "Série de Feu", "Anticipateur")
# The prompt says: "Implémente : Sniper... On Fire... Tennis Expert" IN THE FIRST PROMPT.
# IN THE SECOND PROMPT: "Implémente une logique de 'Checkers'... Trophée 'L'Expert', 'Série de Feu', 'Anticipateur'".
# I should implement the NEW list. I can keep the old ones if compatible or replace them.
# The new ones seem to replace or refine.
# "Série de Feu" is updated to streak >= 7 (was 5).
# "L'Expert" replaces "Tennis Expert" but is generic "Expert on a specific sport".
# "Anticipateur" is new.

class ExpertBadge(BaseBadge):
    slug = "expert"
    name = "L'Expert"
    description = "> 65% de réussite sur un sport spécifique (min. 15 paris)."

    def check_condition(self, stats, bet_selection=None):
        # Must be UserSportStats
        if isinstance(stats, UserSportStats):
            if stats.total_bets >= 15:
                return stats.winrate > 65
        return False

class FireStreakBadge(BaseBadge):
    slug = "serie_de_feu"
    name = "Série de Feu"
    description = "Atteindre une current_streak de 7 victoires."

    def check_condition(self, stats, bet_selection=None):
        # Can be global or sport based? Usually global unless specified.
        # "Atteindre une current_streak de 7 victoires" -> implies Global.
        # But if checking sport stats, it might award per sport.
        # Let's assume Global for the main trophy, but if Sport stats have streak, we could award too?
        # Typically "Series of Fire" is a global user achievement.
        if isinstance(stats, UserGlobalStats):
            return stats.current_streak >= 7
        return False

class AnticipatorBadge(BaseBadge):
    slug = "anticipateur"
    name = "Anticipateur"
    description = "Avoir posté 10 paris plus de 24h avant le coup d'envoi."

    def check_condition(self, stats, bet_selection=None):
        # This requires a query. The stats object doesn't have this count.
        user = stats.user

        # Check if the count matches.
        # We can optimize: Only check if the current bet was > 24h.
        if not bet_selection:
            return False

        if not bet_selection.kickoff_time:
            return False

        # Check if current bet qualifies
        time_diff = bet_selection.kickoff_time - bet_selection.created
        if time_diff < timedelta(hours=24):
            return False

        # Count total qualifying bets for this user
        # We assume valid bets (created < kickoff) are filtered already by logic,
        # but here we specifically look for > 24h gap.
        count = BetSelection.objects.filter(
            ticket__user=user,
            kickoff_time__isnull=False,
            created__lt=F('kickoff_time') - timedelta(hours=24),
            outcome__in=[BetSelection.Outcome.WON, BetSelection.Outcome.LOST, BetSelection.Outcome.VOID]
        ).count()

        return count >= 10

BADGE_REGISTRY = [
    ExpertBadge(),
    FireStreakBadge(),
    AnticipatorBadge(),
]
