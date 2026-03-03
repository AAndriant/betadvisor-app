"""
Adaptive settlement cron — runs every 10 minutes.
Only queries APIs for sports that have PENDING predictions.

Usage:
    python manage.py settle_predictions

Cron setup (every 10 min):
    */10 * * * * cd /app && python manage.py settle_predictions
"""
import logging
from collections import defaultdict
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from bets.prediction_models import Prediction
from bets.sports_api import (
    get_football_fixture,
    get_football_events,
    get_tennis_fixture,
    get_fixture_by_sport,
    is_match_finished,
    is_match_cancelled,
    extract_score,
    verify_prediction,
    SportsAPIError,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Settle pending predictions by checking sports API results (adaptive cron).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be settled without saving.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        self.stdout.write(self.style.NOTICE(
            f"[{timezone.now().isoformat()}] Starting adaptive settlement check..."
        ))

        # 1. Get all pending predictions with an API fixture ID
        pending = Prediction.objects.filter(
            outcome=Prediction.Outcome.PENDING,
            api_fixture_id__isnull=False,
        ).select_related('bet_ticket', 'bet_ticket__author')

        if not pending.exists():
            self.stdout.write(self.style.SUCCESS("No pending predictions. Skipping."))
            return

        self.stdout.write(f"Found {pending.count()} pending predictions to check.")

        # 2. Group by sport + fixture_id to minimize API calls
        grouped = defaultdict(list)
        for pred in pending:
            key = (pred.sport, pred.api_fixture_id)
            grouped[key].append(pred)

        self.stdout.write(
            f"Grouped into {len(grouped)} unique fixtures across "
            f"{len(set(k[0] for k in grouped))} sport(s)."
        )

        # 3. For each unique fixture, check the result
        settled_count = 0
        error_count = 0
        skipped_count = 0

        for (sport, fixture_id), predictions in grouped.items():
            try:
                fixture_data = self._fetch_fixture(sport, fixture_id)
                if fixture_data is None:
                    logger.warning(f"Fixture {fixture_id} ({sport}) not found in API")
                    skipped_count += len(predictions)
                    continue

                # Check if match is cancelled
                if is_match_cancelled(fixture_data, sport):
                    self.stdout.write(
                        f"  ⊘ {sport} fixture {fixture_id} — CANCELLED/POSTPONED"
                    )
                    for pred in predictions:
                        if not dry_run:
                            pred.resolve('VOID', {'reason': 'match_cancelled'})
                        settled_count += 1
                    continue

                # Check if match is finished
                if not is_match_finished(fixture_data, sport):
                    self.stdout.write(
                        f"  ⏳ {sport} fixture {fixture_id} — not finished yet"
                    )
                    skipped_count += len(predictions)
                    continue

                # Match is finished — extract score and resolve predictions
                score = extract_score(fixture_data, sport)
                events = None

                # Get detailed events for football (goalscorers)
                has_goalscorer_preds = any(
                    p.prediction_type == 'GOALSCORER' for p in predictions
                )
                if sport == 'FOOTBALL' and has_goalscorer_preds:
                    try:
                        events = get_football_events(fixture_id)
                    except SportsAPIError:
                        events = None

                self.stdout.write(
                    f"  ✅ {sport} fixture {fixture_id} — "
                    f"Score: {score.get('home')}-{score.get('away')}"
                )

                for pred in predictions:
                    result = verify_prediction(
                        pred.prediction_type,
                        pred.prediction_value,
                        score,
                        events=events,
                    )

                    if not dry_run:
                        pred.resolve(result, {
                            'score': score,
                            'fixture_id': fixture_id,
                        })
                        # Update gamification stats
                        self._update_stats(pred.bet_ticket.author, result)

                    symbol = '✓' if result == 'CORRECT' else '✗' if result == 'INCORRECT' else '?'
                    self.stdout.write(
                        f"    {symbol} {pred.prediction_value} → {result}"
                    )
                    settled_count += 1

            except SportsAPIError as e:
                logger.error(f"API error for {sport} fixture {fixture_id}: {e}")
                error_count += len(predictions)
            except Exception as e:
                logger.exception(f"Unexpected error settling {sport} fixture {fixture_id}: {e}")
                error_count += len(predictions)

        # Summary
        self.stdout.write(self.style.SUCCESS(
            f"\n{'[DRY RUN] ' if dry_run else ''}"
            f"Settlement complete: {settled_count} settled, "
            f"{skipped_count} skipped (not finished), "
            f"{error_count} errors."
        ))

    def _fetch_fixture(self, sport, fixture_id):
        """Fetch fixture data from the appropriate API."""
        if sport == 'FOOTBALL':
            return get_football_fixture(fixture_id)
        elif sport == 'TENNIS':
            return get_tennis_fixture(fixture_id)
        else:
            return get_fixture_by_sport(sport, fixture_id)

    def _update_stats(self, user, result):
        """Update UserGlobalStats after a prediction is resolved."""
        try:
            from gamification.models import UserGlobalStats
            stats, _ = UserGlobalStats.objects.get_or_create(user=user)
            stats.total_bets += 1
            if result == 'CORRECT':
                stats.wins += 1
                stats.current_streak += 1
                if stats.current_streak > stats.max_streak:
                    stats.max_streak = stats.current_streak
            elif result == 'INCORRECT':
                stats.losses += 1
                stats.current_streak = 0
            stats.save()
        except Exception as e:
            logger.error(f"Failed to update stats for {user}: {e}")
