from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models import F
from tickets.models import BetSelection
from gamification.models import UserGlobalStats, UserSportStats, UserBadge
from gamification.badges import BADGE_REGISTRY
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
    stake = bet_selection.stake
    odds = bet_selection.odds

    # Calculate return
    payout = Decimal('0.00')
    if outcome == BetSelection.Outcome.WON:
        payout = stake * odds
    elif outcome == BetSelection.Outcome.VOID:
        payout = stake # Refund
    # LOST = 0

    with transaction.atomic():
        # Lock the bet selection to prevent concurrent processing (double check)
        # However, post_save is already triggered. We should lock the stats rows.
        # We also need to mark bet_selection as processed inside the transaction.

        # Reload bet_selection with lock to ensure 'stats_processed' is still False
        bet_selection = BetSelection.objects.select_for_update().get(id=bet_selection.id)
        if bet_selection.stats_processed:
            return

        # 1. Update Global Stats
        global_stats, _ = UserGlobalStats.objects.select_for_update().get_or_create(user=user)

        # Prepare updates
        updates = {
            'total_bets': F('total_bets') + 1,
            'total_investment': F('total_investment') + stake,
            'total_return': F('total_return') + payout,
        }

        if outcome == BetSelection.Outcome.WON:
            updates['wins'] = F('wins') + 1
            updates['current_win_streak'] = F('current_win_streak') + 1
            # We need to handle max_win_streak.
            # F() cannot conditionally update max_win_streak based on the new current_win_streak easily in one go.
            # So we might need to fetch the current value first, or update it in a second step.
            # But since we have exclusive lock on global_stats (select_for_update), we can safely read and update.
            # However, F() is preferred for atomicity against other processes, but select_for_update already handles that for this row.
            # So we can use python values if we are sure we locked the row.

            # Let's use Python arithmetic since we locked the row.
            global_stats.total_bets += 1
            global_stats.total_investment += stake
            global_stats.total_return += payout
            global_stats.wins += 1
            global_stats.current_win_streak += 1
            if global_stats.current_win_streak > global_stats.max_win_streak:
                global_stats.max_win_streak = global_stats.current_win_streak

        elif outcome == BetSelection.Outcome.LOST:
            updates['losses'] = F('losses') + 1
            updates['current_win_streak'] = 0 # Reset streak

            global_stats.total_bets += 1
            global_stats.total_investment += stake
            global_stats.total_return += payout
            global_stats.losses += 1
            global_stats.current_win_streak = 0

        elif outcome == BetSelection.Outcome.VOID:
            updates['voids'] = F('voids') + 1
            # Void usually doesn't break streak? Or does it?
            # Standard: Void doesn't count for streak, so streak stays same.

            global_stats.total_bets += 1
            global_stats.total_investment += stake
            global_stats.total_return += payout
            global_stats.voids += 1

        global_stats.save()

        # 2. Update Sport Stats
        sport = bet_selection.match.league.sport
        sport_stats, _ = UserSportStats.objects.select_for_update().get_or_create(user=user, sport=sport)

        if outcome == BetSelection.Outcome.WON:
            sport_stats.total_bets += 1
            sport_stats.total_investment += stake
            sport_stats.total_return += payout
            sport_stats.wins += 1
            sport_stats.current_win_streak += 1
            if sport_stats.current_win_streak > sport_stats.max_win_streak:
                sport_stats.max_win_streak = sport_stats.current_win_streak
        elif outcome == BetSelection.Outcome.LOST:
            sport_stats.total_bets += 1
            sport_stats.total_investment += stake
            sport_stats.total_return += payout
            sport_stats.losses += 1
            sport_stats.current_win_streak = 0
        elif outcome == BetSelection.Outcome.VOID:
            sport_stats.total_bets += 1
            sport_stats.total_investment += stake
            sport_stats.total_return += payout
            sport_stats.voids += 1

        sport_stats.save()

        # 3. Mark as processed
        bet_selection.stats_processed = True
        bet_selection.save()

        # 4. Check Badges
        # We check badges against Global Stats and Sport Stats
        for badge in BADGE_REGISTRY:
            # Try with Global Stats
            if badge.check_condition(global_stats, bet_selection):
                badge.award(user)

            # Try with Sport Stats
            if badge.check_condition(sport_stats, bet_selection):
                badge.award(user)
