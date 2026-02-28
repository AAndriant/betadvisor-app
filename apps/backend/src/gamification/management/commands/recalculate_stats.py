from django.core.management.base import BaseCommand
from django.db import transaction
from tickets.models import BetSelection
from gamification.models import UserGlobalStats, UserSportStats, UserBadge
from gamification.signals import process_bet_result

class Command(BaseCommand):
    help = 'Recalculates user stats from scratch based on bet history.'

    def handle(self, *args, **options):
        self.stdout.write("Starting stats recalculation...")

        with transaction.atomic():
            # 1. Clear all existing stats and badges
            self.stdout.write("Clearing existing stats and badges...")
            UserGlobalStats.objects.all().delete()
            UserSportStats.objects.all().delete()
            UserBadge.objects.all().delete()

            # 2. Reset stats_processed flag on all finalized BetSelections
            self.stdout.write("Resetting processed flags...")
            BetSelection.objects.update(stats_processed=False)

            # 3. Iterate over all finalized bets and process them
            # Order by created to respect history evolution (important for streaks)
            bets = BetSelection.objects.filter(
                outcome__in=[
                    BetSelection.Outcome.WON,
                    BetSelection.Outcome.LOST,
                    BetSelection.Outcome.VOID
                ]
            ).order_by('created')

            count = bets.count()
            self.stdout.write(f"Processing {count} bets...")

            for i, bet in enumerate(bets):
                process_bet_result(bet)
                if (i + 1) % 100 == 0:
                    self.stdout.write(f"Processed {i + 1}/{count}")

        self.stdout.write(self.style.SUCCESS("Stats recalculation completed successfully."))
