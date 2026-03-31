"""
Legacy Football API stub — kept for backwards compatibility.

⚠️  This module is DEPRECATED.  All real API calls now go through
    bets/sports_api.py (multi-sport, API-Sports.io).

The class below returns hardcoded mock data for development/testing.
"""

from django.conf import settings


class FootballAPI:
    """Thin stub returning mock data. Do NOT use in production."""

    BASE_URL = "https://v3.football.api-sports.io"

    def __init__(self):
        self.headers = {
            'x-rapidapi-key': getattr(settings, 'API_SPORTS_KEY', ''),
            'x-rapidapi-host': 'v3.football.api-sports.io',
        }

    def fetch_leagues(self):
        """Return mock league data (dev only)."""
        return [
            {
                "league": {"id": 39, "name": "Premier League", "type": "League"},
                "country": {"name": "England", "code": "GB"},
            },
            {
                "league": {"id": 140, "name": "La Liga", "type": "League"},
                "country": {"name": "Spain", "code": "ES"},
            },
            {
                "league": {"id": 61, "name": "Ligue 1", "type": "League"},
                "country": {"name": "France", "code": "FR"},
            },
        ]

    def fetch_fixtures(self, date_str):
        """Return mock fixture data (dev only)."""
        return [
            {
                "fixture": {
                    "id": 1001,
                    "date": f"{date_str}T20:00:00+00:00",
                    "venue": {"name": "Old Trafford"},
                },
                "league": {"id": 39, "name": "Premier League"},
                "teams": {
                    "home": {"id": 33, "name": "Manchester United"},
                    "away": {"id": 34, "name": "Newcastle"},
                },
            }
        ]
