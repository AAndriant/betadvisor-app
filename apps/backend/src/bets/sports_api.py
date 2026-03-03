"""
Sports API integration for auto-settlement.
Uses API-Sports (api-sports.io) for 9 sports + API-Tennis for tennis.

Both APIs use the same authentication: x-apisports-key header.
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# API-Sports base URLs per sport
API_SPORTS_HOSTS = {
    'FOOTBALL': 'https://v3.football.api-sports.io',
    'BASKETBALL': 'https://v1.basketball.api-sports.io',
    'RUGBY': 'https://v1.rugby.api-sports.io',
    'VOLLEYBALL': 'https://v1.volleyball.api-sports.io',
    'HANDBALL': 'https://v1.handball.api-sports.io',
    'HOCKEY': 'https://v1.hockey.api-sports.io',
    'BASEBALL': 'https://v1.baseball.api-sports.io',
    'FORMULA1': 'https://v1.formula-1.api-sports.io',
    'MMA': 'https://v1.mma.api-sports.io',
}

API_TENNIS_HOST = 'https://v1.tennis.api-sports.io'


class SportsAPIError(Exception):
    pass


def _get_api_key():
    key = getattr(settings, 'API_SPORTS_KEY', '')
    if not key:
        raise SportsAPIError("API_SPORTS_KEY not configured in settings")
    return key


def _api_request(host, endpoint, params=None):
    """Make a GET request to an api-sports.io API."""
    api_key = _get_api_key()
    url = f"{host}/{endpoint}"
    headers = {
        'x-apisports-key': api_key,
    }
    try:
        response = requests.get(url, headers=headers, params=params or {}, timeout=15)
        response.raise_for_status()
        data = response.json()

        # Check for API-level errors
        if data.get('errors') and len(data['errors']) > 0:
            logger.warning(f"API warning for {url}: {data['errors']}")

        return data.get('response', [])
    except requests.RequestException as e:
        logger.error(f"Sports API request failed: {url} — {e}")
        raise SportsAPIError(f"Request failed: {e}")


# ─── Football ───────────────────────────────────────────
def get_football_fixtures_by_date(date_str):
    """Get all fixtures for a date (YYYY-MM-DD)."""
    return _api_request(
        API_SPORTS_HOSTS['FOOTBALL'],
        'fixtures',
        {'date': date_str}
    )


def get_football_fixture(fixture_id):
    """Get a single fixture by ID."""
    results = _api_request(
        API_SPORTS_HOSTS['FOOTBALL'],
        'fixtures',
        {'id': fixture_id}
    )
    return results[0] if results else None


def get_football_events(fixture_id):
    """Get events (goals, cards, subs) for a fixture."""
    return _api_request(
        API_SPORTS_HOSTS['FOOTBALL'],
        'fixtures/events',
        {'fixture': fixture_id}
    )


def search_football_fixture(home_team, away_team, date_str):
    """Search for a fixture by team names and date."""
    fixtures = get_football_fixtures_by_date(date_str)
    for fixture in fixtures:
        teams = fixture.get('teams', {})
        home = teams.get('home', {}).get('name', '').lower()
        away = teams.get('away', {}).get('name', '').lower()
        if (home_team.lower() in home or home in home_team.lower()) and \
           (away_team.lower() in away or away in away_team.lower()):
            return fixture
    return None


# ─── Tennis ─────────────────────────────────────────────
def get_tennis_fixtures_by_date(date_str):
    """Get all tennis fixtures for a date."""
    return _api_request(API_TENNIS_HOST, 'games', {'date': date_str})


def get_tennis_fixture(fixture_id):
    """Get a single tennis fixture by ID."""
    results = _api_request(API_TENNIS_HOST, 'games', {'id': fixture_id})
    return results[0] if results else None


# ─── Generic (Basketball, Rugby, etc.) ──────────────────
def get_fixtures_by_sport_and_date(sport, date_str):
    """Get fixtures for any API-Sports sport by date."""
    host = API_SPORTS_HOSTS.get(sport)
    if not host:
        logger.warning(f"No API host configured for sport: {sport}")
        return []
    return _api_request(host, 'games', {'date': date_str})


def get_fixture_by_sport(sport, fixture_id):
    """Get a single fixture for any sport."""
    host = API_SPORTS_HOSTS.get(sport)
    if not host:
        return None
    results = _api_request(host, 'games', {'id': fixture_id})
    return results[0] if results else None


# ─── Result Verification ────────────────────────────────
def is_match_finished(fixture_data, sport='FOOTBALL'):
    """Check if a match is finished based on the fixture data."""
    if sport == 'FOOTBALL':
        status = fixture_data.get('fixture', {}).get('status', {}).get('short', '')
        return status in ('FT', 'AET', 'PEN')  # Full Time, After Extra Time, Penalties
    elif sport == 'TENNIS':
        status = fixture_data.get('status', {}).get('short', '')
        return status in ('FT', 'Finished')
    else:
        # Generic: look for common finished indicators
        status_data = fixture_data.get('status', {})
        if isinstance(status_data, dict):
            short = status_data.get('short', '')
            return short in ('FT', 'AP', 'Finished', 'AOT')
        return False


def is_match_cancelled(fixture_data, sport='FOOTBALL'):
    """Check if a match was cancelled/postponed."""
    if sport == 'FOOTBALL':
        status = fixture_data.get('fixture', {}).get('status', {}).get('short', '')
        return status in ('PST', 'CANC', 'ABD', 'WO')
    else:
        status_data = fixture_data.get('status', {})
        if isinstance(status_data, dict):
            short = status_data.get('short', '')
            return short in ('PST', 'CANC', 'Cancelled', 'Postponed')
        return False


def extract_score(fixture_data, sport='FOOTBALL'):
    """Extract the final score from fixture data."""
    if sport == 'FOOTBALL':
        goals = fixture_data.get('goals', {})
        return {
            'home': goals.get('home'),
            'away': goals.get('away'),
        }
    elif sport == 'TENNIS':
        scores = fixture_data.get('scores', {})
        return {
            'home': scores.get('home'),
            'away': scores.get('away'),
            'sets': fixture_data.get('periods', {}),
        }
    elif sport in ('BASKETBALL', 'HANDBALL', 'VOLLEYBALL', 'HOCKEY'):
        scores = fixture_data.get('scores', {})
        return {
            'home': scores.get('home', {}).get('total'),
            'away': scores.get('away', {}).get('total'),
        }
    return {}


def verify_prediction(prediction_type, prediction_value, score, events=None):
    """
    Verify a prediction against the actual result.
    Returns 'CORRECT', 'INCORRECT', or 'UNVERIFIABLE'.
    """
    home = score.get('home')
    away = score.get('away')

    if home is None or away is None:
        return 'UNVERIFIABLE'

    value = prediction_value.strip().upper()

    if prediction_type == 'MATCH_RESULT':
        # 1 (Home), N (Draw), 2 (Away)
        if value in ('1', 'HOME', 'HOME WIN', 'DOMICILE'):
            return 'CORRECT' if home > away else 'INCORRECT'
        elif value in ('N', 'X', 'DRAW', 'NUL', 'MATCH NUL'):
            return 'CORRECT' if home == away else 'INCORRECT'
        elif value in ('2', 'AWAY', 'AWAY WIN', 'EXTÉRIEUR', 'EXTERIEUR'):
            return 'CORRECT' if away > home else 'INCORRECT'

    elif prediction_type == 'OVER_UNDER':
        total = home + away
        if 'OVER' in value:
            try:
                threshold = float(value.replace('OVER', '').replace('+', '').strip())
                return 'CORRECT' if total > threshold else 'INCORRECT'
            except ValueError:
                return 'UNVERIFIABLE'
        elif 'UNDER' in value:
            try:
                threshold = float(value.replace('UNDER', '').replace('-', '').strip())
                return 'CORRECT' if total < threshold else 'INCORRECT'
            except ValueError:
                return 'UNVERIFIABLE'

    elif prediction_type == 'BTTS':
        if value in ('YES', 'OUI', 'BTTS YES'):
            return 'CORRECT' if home > 0 and away > 0 else 'INCORRECT'
        elif value in ('NO', 'NON', 'BTTS NO'):
            return 'CORRECT' if home == 0 or away == 0 else 'INCORRECT'

    elif prediction_type == 'DOUBLE_CHANCE':
        if value in ('1X', 'X1'):
            return 'CORRECT' if home >= away else 'INCORRECT'
        elif value in ('X2', '2X'):
            return 'CORRECT' if away >= home else 'INCORRECT'
        elif value in ('12', '21'):
            return 'CORRECT' if home != away else 'INCORRECT'

    elif prediction_type == 'CORRECT_SCORE':
        try:
            parts = value.replace('-', ' ').replace(':', ' ').split()
            pred_home, pred_away = int(parts[0]), int(parts[1])
            return 'CORRECT' if home == pred_home and away == pred_away else 'INCORRECT'
        except (ValueError, IndexError):
            return 'UNVERIFIABLE'

    elif prediction_type == 'WINNER':
        # Generic winner — for tennis, MMA, etc.
        # value should contain the winner's name fragment
        # We compare with score: higher score wins
        if home > away:
            # Home won — check if prediction value matches home
            return 'CORRECT'  # Requires name matching (done in settlement command)
        elif away > home:
            return 'INCORRECT'  # Flipped in settlement command based on name
        return 'UNVERIFIABLE'

    elif prediction_type == 'GOALSCORER':
        # Check if a player scored — requires events data
        if events:
            scorer_name = value.lower()
            for event in events:
                if event.get('type') == 'Goal':
                    player = event.get('player', {}).get('name', '').lower()
                    if scorer_name in player or player in scorer_name:
                        return 'CORRECT'
            return 'INCORRECT'
        return 'UNVERIFIABLE'

    elif prediction_type == 'TOTAL_POINTS':
        total = home + away
        if 'OVER' in value or '+' in value:
            try:
                threshold = float(
                    value.replace('OVER', '').replace('+', '').replace('TOTAL', '').strip()
                )
                return 'CORRECT' if total > threshold else 'INCORRECT'
            except ValueError:
                return 'UNVERIFIABLE'
        elif 'UNDER' in value or '-' in value:
            try:
                threshold = float(
                    value.replace('UNDER', '').replace('-', '').replace('TOTAL', '').strip()
                )
                return 'CORRECT' if total < threshold else 'INCORRECT'
            except ValueError:
                return 'UNVERIFIABLE'

    return 'UNVERIFIABLE'
