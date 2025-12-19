from abc import ABC, abstractmethod
from decimal import Decimal
from gamification.models import UserBadge

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

class SniperBadge(BaseBadge):
    slug = "sniper"
    name = "Sniper"
    description = "Winrate > 70% sur au moins 20 paris."

    def check_condition(self, stats, bet_selection=None):
        # We need to make sure we are checking global stats or sport stats?
        # Prompt says "Winrate > 70% sur au moins 20 paris".
        # Assuming Global Stats for simplicity unless specified.
        # But if it is a sport badge, we should check sport stats.
        # The prompt examples: "Sniper", "On Fire", "Tennis Expert".
        # "Tennis Expert" implies sport specific. "Sniper" and "On Fire" sound global.

        # We will check based on the stats object passed.
        # However, the calling code needs to decide which stats to pass.
        # I will design the badge to expect a specific type of stats or handle both if they share interface.
        # Both share total_bets and winrate property.

        if stats.total_bets >= 20:
            return stats.winrate > 70
        return False

class OnFireBadge(BaseBadge):
    slug = "on_fire"
    name = "On Fire"
    description = "current_win_streak >= 5"

    def check_condition(self, stats, bet_selection=None):
        return stats.current_win_streak >= 5

class TennisExpertBadge(BaseBadge):
    slug = "tennis_expert"
    name = "Tennis Expert"
    description = "total_bets > 50 sur le sport 'Tennis'."

    def check_condition(self, stats, bet_selection=None):
        # This badge is sport specific.
        # We need to check if the stats passed are for Tennis.
        # Or we check the user's global tennis stats if we are not passed sport stats?
        # The trigger will pass the updated stats.
        # If the trigger passes UserGlobalStats, we can't check Tennis specific things easily unless we query UserSportStats.

        # Better design: Pass 'user' and query what is needed, or Pass 'stats' and check if it is applicable.
        # For 'Tennis Expert', we need UserSportStats where sport.name = 'Tennis'.

        from gamification.models import UserSportStats

        user = stats.user
        # We can optimize by checking if the current bet was Tennis.
        if bet_selection and bet_selection.match.league.sport.name == "Tennis":
            # Check the sport stats for this user and Tennis
            # We can use the passed stats if they are UserSportStats and for Tennis.
            if isinstance(stats, UserSportStats) and stats.sport.name == "Tennis":
                 return stats.total_bets > 50

            # Fallback if we passed GlobalStats but want to check Tennis
            try:
                sport_stats = UserSportStats.objects.get(user=user, sport__name="Tennis")
                return sport_stats.total_bets > 50
            except UserSportStats.DoesNotExist:
                return False

        return False

BADGE_REGISTRY = [
    SniperBadge(),
    OnFireBadge(),
    TennisExpertBadge(),
]
