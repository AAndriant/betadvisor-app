from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from sports.models import Sport, League, Match
from sports.services import FootballAPI
from datetime import date

class Command(BaseCommand):
    help = 'Syncs sports data (leagues and fixtures) from external API'

    def handle(self, *args, **options):
        self.stdout.write("Starting sports sync...")
        api = FootballAPI()

        # 1. Sync Leagues
        self.stdout.write("Fetching leagues...")
        leagues_data = api.fetch_leagues()
        
        # Ensure 'Football' sport exists
        football, _ = Sport.objects.get_or_create(name="Football")

        for item in leagues_data:
            l_data = item['league']
            c_data = item['country']
            
            League.objects.update_or_create(
                name=l_data['name'],
                sport=football,
                defaults={
                    'country': c_data['name']
                }
            )
        self.stdout.write(f"Synced {len(leagues_data)} leagues.")

        # 2. Sync Fixtures (for today)
        today = date.today().isoformat()
        self.stdout.write(f"Fetching fixtures for {today}...")
        fixtures_data = api.fetch_fixtures(today)

        for item in fixtures_data:
            f_data = item['fixture']
            l_data = item['league']
            t_data = item['teams']

            # Find league
            try:
                league = League.objects.get(name=l_data['name'], sport=football)
            except League.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"League {l_data['name']} not found, skipping match."))
                continue

            Match.objects.update_or_create(
                home_team=t_data['home']['name'],
                away_team=t_data['away']['name'],
                date_time=parse_datetime(f_data['date']),
                league=league,
                defaults={}
            )
        
        self.stdout.write(f"Synced {len(fixtures_data)} matches.")
        self.stdout.write(self.style.SUCCESS("Sports sync complete."))
