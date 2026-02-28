from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count, Q, F
from tickets.models import BetSelection
from gamification.models import UserGlobalStats

def calculate_reputation_score(user):
    """
    Calculates the reputation score (0-100) based on Yield and Winrate of the last 30 days.
    Also updates the profile_halo_color.
    """
    now = timezone.now()
    thirty_days_ago = now - timezone.timedelta(days=30)

    # Query bets for the last 30 days that are finalized (WON/LOST) and valid (created < kickoff)
    bets = BetSelection.objects.filter(
        ticket__user=user,
        outcome__in=[BetSelection.Outcome.WON, BetSelection.Outcome.LOST],
        created__gte=thirty_days_ago,
        # We assume invalid bets (created > kickoff) are already excluded from 'stats_processed' logic
        # but to be safe and accurate for the score, we filter them here too.
        # Note: If kickoff_time is null, we assume valid or ignore?
        # Strict rule: "Seuls les paris dont created_at < kickoff_time sont éligibles"
        # So if kickoff_time is NULL, strictly speaking we can't verify, so maybe exclude?
        # Or assume validated bets are fine. Let's strictly require kickoff_time check if set.
        # If kickoff_time is null, we might be lenient or strict. Given "Rigueur & Performance", strict is better.
        # But for now let's check `created < kickoff_time` only if kickoff_time exists, or rely on the signal to populate it.
        # Actually, the prompt says "Seuls les paris dont created_at < kickoff_time sont éligibles aux statistiques".
        # So we should filter them.
        kickoff_time__isnull=False,
        created__lt=F('kickoff_time')
    )

    # Aggregation
    # We need count of bets (total_bets)
    # Count of wins
    # Sum of odds for wins (units_returned)

    stats = bets.aggregate(
        total=Count('id'),
        wins=Count('id', filter=Q(outcome=BetSelection.Outcome.WON)),
        sum_odds=Sum('odds', filter=Q(outcome=BetSelection.Outcome.WON))
    )

    total_bets = stats['total'] or 0
    wins = stats['wins'] or 0
    sum_odds = stats['sum_odds'] or Decimal('0.00')

    if total_bets == 0:
        return 0 # No reputation if no activity

    # Calculate Winrate %
    # Winrate = Wins / Total Bets * 100
    winrate = (Decimal(wins) / Decimal(total_bets)) * 100

    # Calculate Yield % (ROI)
    # Net Profit = Sum Odds - Total Bets (since 1 unit stake)
    # Yield = Net Profit / Total Bets * 100
    net_profit = sum_odds - Decimal(total_bets)
    yield_val = (net_profit / Decimal(total_bets)) * 100

    # Scoring Formula (0-100)
    # Design a formula that rewards high yield and decent winrate.
    # Yield is the most important metric for bettors.
    # Winrate is secondary but important for stability.

    # Proposal:
    # Score = min(100, max(0, Base + YieldFactor + WinrateFactor))
    # Let's calibrate:
    # A Yield of 10% is excellent. A Winrate of 55% is good (at avg odds ~2.0).
    # A Yield of 20% is godlike.
    # A Yield of -5% is bad.

    # Simple weighted approach normalized to 0-100?
    # Let's assign points based on ranges.

    # Winrate Score (0-40 points)
    # < 30%: 0
    # 30-40%: 10
    # 40-50%: 20
    # 50-60%: 30
    # > 60%: 40

    wr_score = 0
    if winrate > 60: wr_score = 40
    elif winrate > 50: wr_score = 30
    elif winrate > 40: wr_score = 20
    elif winrate > 30: wr_score = 10

    # Yield Score (0-60 points)
    # < -10%: 0
    # -10% to 0%: 10
    # 0% to 5%: 30
    # 5% to 10%: 45
    # > 10%: 60

    yield_score = 0
    if yield_val > 10: yield_score = 60
    elif yield_val > 5: yield_score = 45
    elif yield_val > 0: yield_score = 30
    elif yield_val > -10: yield_score = 10

    final_score = wr_score + yield_score

    return final_score

def get_halo_color(score):
    if score >= 80: return 'gold'
    if score >= 60: return 'silver'
    if score >= 40: return 'bronze'
    return 'none'

def update_reputation(user):
    from gamification.models import UserGlobalStats
    score = calculate_reputation_score(user)
    color = get_halo_color(score)

    UserGlobalStats.objects.filter(user=user).update(
        reputation_score=score,
        profile_halo_color=color
    )
