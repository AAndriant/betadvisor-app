from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models import F
from tickets.models import BetSelection
from gamification.models import UserGlobalStats, UserSportStats, UserBadge
from gamification.badges import BADGE_REGISTRY
from gamification.utils import update_reputation
from users.models import CustomUser

@receiver(post_save, sender=BetSelection)
def update_user_stats(sender, instance, created, **kwargs):
    # Only process if outcome is final (WON, LOST, VOID) and not yet processed
    if instance.outcome in [BetSelection.Outcome.WON, BetSelection.Outcome.LOST, BetSelection.Outcome.VOID]:
        if not instance.stats_processed:
            process_bet_result(instance)

def process_bet_result(bet_selection):
    user = bet_selection.ticket.user
    outcome = bet_selection.outcome
    odds = bet_selection.odds
    created_at = bet_selection.created
    kickoff_time = bet_selection.kickoff_time

    # Validation Temporelle: Ignore stats if created >= kickoff_time
    is_valid_time = True
    if kickoff_time and created_at >= kickoff_time:
        is_valid_time = False

    with transaction.atomic():
        # Lock the bet selection
        bet_selection = BetSelection.objects.select_for_update().get(id=bet_selection.id)
        if bet_selection.stats_processed:
            return

        # Mark as processed immediately to avoid re-entry if something fails later but we want to consume the event
        # Actually, we should mark it at the end of transaction.

        if not is_valid_time:
            # Just mark as processed and exit
            bet_selection.stats_processed = True
            bet_selection.save()
            return

        # 1. Update Global Stats
        global_stats, _ = UserGlobalStats.objects.select_for_update().get_or_create(user=user)

        # Unit based calculation: 1 unit per bet.
        # units_returned: if WON => odds. if VOID => 1. if LOST => 0.

        units_returned_delta = Decimal('0.00')

        global_stats.total_bets += 1

        if outcome == BetSelection.Outcome.WON:
            units_returned_delta = odds
            global_stats.wins += 1
            global_stats.current_streak += 1
            if global_stats.current_streak > global_stats.max_streak:
                global_stats.max_streak = global_stats.current_streak

        elif outcome == BetSelection.Outcome.LOST:
            global_stats.losses += 1
            global_stats.current_streak = 0

        elif outcome == BetSelection.Outcome.VOID:
            # Void returns the unit.
            units_returned_delta = Decimal('1.00')
            global_stats.voids += 1
            # Void usually keeps streak intact or ignores it?
            # Standard: Streak implies consecutive wins. A void is neither win nor loss.
            # Usually streak is not reset but not incremented.

        global_stats.units_returned += units_returned_delta
        global_stats.save()

        # 2. Update Sport Stats
        sport = bet_selection.match.league.sport
        sport_stats, _ = UserSportStats.objects.select_for_update().get_or_create(user=user, sport=sport)

        sport_stats.total_bets += 1

        if outcome == BetSelection.Outcome.WON:
            sport_stats.units_returned += odds
            sport_stats.wins += 1
            sport_stats.current_streak += 1
            if sport_stats.current_streak > sport_stats.max_streak:
                sport_stats.max_streak = sport_stats.current_streak

        elif outcome == BetSelection.Outcome.LOST:
            sport_stats.losses += 1
            sport_stats.current_streak = 0

        elif outcome == BetSelection.Outcome.VOID:
            sport_stats.units_returned += Decimal('1.00')
            sport_stats.voids += 1

        sport_stats.save()

        # 3. Mark as processed
        bet_selection.stats_processed = True
        bet_selection.save()

        # 4. Calculate Halo / Reputation (Real-time)
        # This function updates the UserGlobalStats row again (or specific fields).
        # Since we are in atomic block, it is safe.
        update_reputation(user)

        # Reload global stats to get updated reputation/halo for badges if needed
        global_stats.refresh_from_db()

        # 5. Check Badges
        # We check badges against Global Stats and Sport Stats
        for badge in BADGE_REGISTRY:
            # Try with Global Stats
            if badge.check_condition(global_stats, bet_selection):
                badge.award(user)

            # Try with Sport Stats
            if badge.check_condition(sport_stats, bet_selection):
                badge.award(user)
