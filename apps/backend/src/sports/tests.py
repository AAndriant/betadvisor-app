from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from sports.management.commands import sync_sports
from sports.models import League, Match, Sport


class SyncSportsCommandTests(TestCase):
    def test_sync_sports_batches_league_lookup_and_preserves_behavior(self):
        football = Sport.objects.create(name='Football')
        League.objects.create(name='Premier League', sport=football, country='Old Country')

        api = self._mock_api()

        with patch.object(sync_sports, 'FootballAPI', return_value=api):
            output = StringIO()
            call_command('sync_sports', stdout=output)

        self.assertEqual(League.objects.filter(sport=football).count(), 2)
        self.assertEqual(
            League.objects.get(sport=football, name='Premier League').country,
            'England',
        )
        self.assertTrue(
            Match.objects.filter(
                league__name='Premier League',
                home_team='Manchester United',
                away_team='Newcastle',
            ).exists()
        )
        self.assertIn('Sports sync complete.', output.getvalue())

    @staticmethod
    def _mock_api():
        class MockFootballAPI:
            def fetch_leagues(self):
                return [
                    {
                        'league': {'id': 39, 'name': 'Premier League', 'type': 'League'},
                        'country': {'name': 'England', 'code': 'GB'},
                    },
                    {
                        'league': {'id': 140, 'name': 'La Liga', 'type': 'League'},
                        'country': {'name': 'Spain', 'code': 'ES'},
                    },
                ]

            def fetch_fixtures(self, date_str):
                return [
                    {
                        'fixture': {
                            'id': 1001,
                            'date': f'{date_str}T20:00:00+00:00',
                        },
                        'league': {'id': 39, 'name': 'Premier League'},
                        'teams': {
                            'home': {'id': 33, 'name': 'Manchester United'},
                            'away': {'id': 34, 'name': 'Newcastle'},
                        },
                    },
                    {
                        'fixture': {
                            'id': 1002,
                            'date': f'{date_str}T21:00:00+00:00',
                        },
                        'league': {'id': 999, 'name': 'Unknown League'},
                        'teams': {
                            'home': {'id': 1, 'name': 'A'},
                            'away': {'id': 2, 'name': 'B'},
                        },
                    },
                ]

        return MockFootballAPI()
