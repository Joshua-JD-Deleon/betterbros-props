"""
SportsGameOdds API client for fetching NFL player props.

API Documentation: https://api.sportsgameodds.com/v2
"""

from typing import Dict, List, Optional
import pandas as pd
import httpx
import time
from pathlib import Path
from datetime import datetime, timedelta
import os

# Rate limiting
RATE_LIMIT_DELAY = 1.0  # seconds between requests


class SportGameOddsClient:
    """
    Client for SportsGameOdds API to fetch NFL player props.

    Advantages over The Odds API:
    - More comprehensive player props
    - Better player data (IDs, full names)
    - Team-level data integration
    - More granular oddIDs
    """

    BASE_URL = "https://api.sportsgameodds.com/v2"
    SPORT = "NFL"

    # Player prop markets available
    PROP_MARKETS = [
        "player-points",
        "player-rebounds",
        "player-assists",
        "player-passing-yards",
        "player-rushing-yards",
        "player-receiving-yards",
        "player-passing-touchdowns",
        "player-rushing-touchdowns",
        "player-receptions",
        "player-completions",
        "player-pass-attempts",
        "player-interceptions",
        "player-anytime-touchdown",
        "player-first-touchdown",
        "player-field-goals",
        "player-kicking-points",
    ]

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize SportsGameOdds API client.

        Args:
            api_key: API key from SportsGameOdds (or from env var SPORTGAMEODDS_API_KEY)
        """
        self.api_key = api_key or os.getenv("SPORTGAMEODDS_API_KEY")
        if not self.api_key:
            raise ValueError("SPORTGAMEODDS_API_KEY not found in environment or passed as argument")

        self.client = httpx.Client(timeout=30.0)
        self.last_request_time = 0
        self.cache_dir = Path("data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()

    def _get_cache_path(self, endpoint: str, params: dict) -> Path:
        """Generate cache file path for request."""
        import hashlib
        cache_string = f"{endpoint}_{'_'.join(f'{k}={v}' for k, v in sorted(params.items()))}"
        cache_hash = hashlib.md5(cache_string.encode()).hexdigest()
        return self.cache_dir / f"sportgameodds_{cache_hash}.parquet"

    def _load_from_cache(self, cache_path: Path, ttl_hours: int = 1) -> Optional[pd.DataFrame]:
        """Load data from cache if it exists and is fresh."""
        if not cache_path.exists():
            return None

        # Check age
        file_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        if file_age > timedelta(hours=ttl_hours):
            return None

        try:
            return pd.read_parquet(cache_path)
        except Exception as e:
            print(f"Warning: Failed to load cache: {e}")
            return None

    def _save_to_cache(self, data: pd.DataFrame, cache_path: Path):
        """Save data to cache."""
        try:
            data.to_parquet(cache_path, index=False)
        except Exception as e:
            print(f"Warning: Failed to save cache: {e}")

    def _make_request(self, endpoint: str, params: dict = None) -> dict:
        """
        Make API request with rate limiting and error handling.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response as dict
        """
        self._rate_limit()

        url = f"{self.BASE_URL}/{endpoint}"
        headers = {
            "X-API-Key": self.api_key
        }

        try:
            response = self.client.get(url, headers=headers, params=params or {})
            response.raise_for_status()

            # Log API usage if available in headers
            remaining = response.headers.get("x-ratelimit-remaining")
            if remaining:
                print(f"API Usage: {remaining} requests remaining")

            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid API key for SportsGameOdds")
            elif e.response.status_code == 429:
                raise ValueError("Rate limit exceeded. Wait before making more requests.")
            else:
                raise ValueError(f"API error: {e.response.status_code} - {e.response.text}")

        except Exception as e:
            raise ValueError(f"Request failed: {str(e)}")

    def get_upcoming_games(self, sport: str = "NFL") -> List[Dict]:
        """
        Get list of upcoming games for a sport.

        Args:
            sport: Sport key (NFL, NBA, MLB)

        Returns:
            List of game dictionaries
        """
        endpoint = f"events/{sport}"
        params = {}

        cache_path = self._get_cache_path(endpoint, params)

        # Try cache first (1 hour TTL)
        cached = self._load_from_cache(cache_path, ttl_hours=1)
        if cached is not None:
            return cached.to_dict('records')

        # Fetch from API
        data = self._make_request(endpoint, params)

        # Convert to DataFrame for caching
        if data and isinstance(data, list):
            df = pd.DataFrame(data)
            self._save_to_cache(df, cache_path)
            return data
        elif data and 'events' in data:
            df = pd.DataFrame(data['events'])
            self._save_to_cache(df, cache_path)
            return data['events']

        return []

    def get_props_for_event(
        self,
        event_id: str,
        markets: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Get player props for a specific game.

        Args:
            event_id: Event ID from get_upcoming_games()
            markets: List of prop markets to fetch (default: all available)

        Returns:
            DataFrame with columns:
                - player_name
                - prop_type
                - line
                - over_odds (American odds)
                - under_odds (American odds)
                - bookmaker
                - game_id
                - game_time
                - home_team
                - away_team
        """
        endpoint = f"odds/event/{event_id}"
        params = {}

        cache_path = self._get_cache_path(endpoint, params)

        # Try cache first (30 min TTL for live odds)
        cached = self._load_from_cache(cache_path, ttl_hours=0.5)
        if cached is not None:
            return cached

        # Fetch from API
        try:
            data = self._make_request(endpoint, params)
        except ValueError as e:
            if "404" in str(e):
                print(f"  ⚠ No odds available for event {event_id} yet")
                return pd.DataFrame()
            raise

        # Parse response into props DataFrame
        props = self._parse_props_response(data, event_id)

        # Cache results
        if not props.empty:
            self._save_to_cache(props, cache_path)

        return props

    def _parse_props_response(self, data: dict, event_id: str) -> pd.DataFrame:
        """
        Parse SportsGameOdds API response into our standard prop format.

        SportsGameOdds format:
        {
            "event": {
                "eventId": "...",
                "startTime": "2024-10-13T17:00:00Z",
                "homeTeam": {"name": "Kansas City Chiefs"},
                "awayTeam": {"name": "Denver Broncos"}
            },
            "odds": [
                {
                    "oddId": "player-passing-yards-mahomes-over-275.5",
                    "market": "player-passing-yards",
                    "player": {
                        "playerId": "mahomes_patrick",
                        "name": "Patrick Mahomes"
                    },
                    "line": 275.5,
                    "overOdds": -110,
                    "underOdds": -110,
                    "bookmaker": "draftkings"
                }
            ]
        }
        """
        props_list = []

        # Extract event info
        event = data.get("event", {})
        game_time = event.get("startTime")
        home_team = event.get("homeTeam", {}).get("name")
        away_team = event.get("awayTeam", {}).get("name")

        # Extract odds/props
        odds_list = data.get("odds", [])

        for odd in odds_list:
            # Extract player info
            player_info = odd.get("player", {})
            player_name = player_info.get("name")
            player_id = player_info.get("playerId")

            if not player_name:
                continue

            # Extract prop details
            market = odd.get("market", "")
            prop_type = self._normalize_prop_type(market)
            line = odd.get("line")
            over_odds = odd.get("overOdds")
            under_odds = odd.get("underOdds")
            bookmaker = odd.get("bookmaker", "unknown")

            # Only include if we have both over and under odds
            if over_odds is not None and under_odds is not None and line is not None:
                # Infer position from prop_type
                position = self._infer_position(prop_type)

                props_list.append({
                    "player_id": player_id or player_name.lower().replace(" ", "_").replace(".", ""),
                    "player_name": player_name,
                    "prop_type": prop_type,
                    "line": line,
                    "over_odds": over_odds,
                    "under_odds": under_odds,
                    "bookmaker": bookmaker,
                    "game_id": event_id,
                    "game_time": pd.to_datetime(game_time) if game_time else None,
                    "home_team": home_team,
                    "away_team": away_team,
                    "team": None,  # Would need roster data to determine
                    "position": position,
                    "opponent": None,
                })

        return pd.DataFrame(props_list) if props_list else pd.DataFrame()

    def _normalize_prop_type(self, market: str) -> str:
        """Convert SportsGameOdds market key to our prop_type format."""
        # Remove 'player-' prefix and convert dashes to underscores
        prop = market.replace("player-", "").replace("-", "_")

        # Map to our standard naming
        mapping = {
            "passing_yards": "passing_yards",
            "passing_touchdowns": "passing_tds",
            "passing_tds": "passing_tds",
            "completions": "passing_completions",
            "pass_attempts": "passing_attempts",
            "interceptions": "passing_interceptions",
            "rushing_yards": "rushing_yards",
            "rushing_touchdowns": "rushing_tds",
            "rushing_attempts": "rushing_attempts",
            "receiving_yards": "receiving_yards",
            "receptions": "receptions",
            "anytime_touchdown": "anytime_touchdown",
            "first_touchdown": "first_touchdown",
            "field_goals": "field_goals_made",
            "kicking_points": "kicking_points",
        }

        return mapping.get(prop, prop)

    def _infer_position(self, prop_type: str) -> str:
        """Infer player position from prop type."""
        if 'passing' in prop_type or 'completions' in prop_type:
            return 'QB'
        elif 'rushing' in prop_type:
            return 'RB'
        elif 'receiving' in prop_type or 'receptions' in prop_type:
            return 'WR/TE'
        elif 'kicking' in prop_type or 'field_goal' in prop_type:
            return 'K'
        elif 'touchdown' in prop_type:
            return 'TD (Any)'
        else:
            return 'Unknown'

    def fetch_all_current_props(
        self,
        sport: str = "NFL",
        max_games: Optional[int] = None,
        game_time_filter: str = "Upcoming Only"
    ) -> pd.DataFrame:
        """
        Fetch props for all upcoming games.

        Args:
            sport: Sport key (NFL, NBA, MLB)
            max_games: Limit number of games to fetch
            game_time_filter: Filter games by start time
                - "Upcoming Only": Only games that haven't started yet
                - "Include Started Games": Games that started today or later
                - "All Games": All games including past ones

        Returns:
            DataFrame with all props from all games
        """
        print(f"Fetching upcoming {sport} games...")
        games = self.get_upcoming_games(sport=sport)

        if not games:
            print("No upcoming games found")
            return pd.DataFrame()

        # Filter games by time
        if game_time_filter != "All Games":
            from datetime import timezone
            now = datetime.now(timezone.utc)
            print(f"\nCurrent time (UTC): {now}")
            print(f"Time filter mode: {game_time_filter}")

            filtered_games = []
            for game in games:
                start_time_str = game.get("startTime") or game.get("commence_time")
                home = game.get("homeTeam", {}).get("name", "Unknown") if isinstance(game.get("homeTeam"), dict) else game.get("home_team", "Unknown")
                away = game.get("awayTeam", {}).get("name", "Unknown") if isinstance(game.get("awayTeam"), dict) else game.get("away_team", "Unknown")

                if not start_time_str:
                    print(f"  ⚠ {away} @ {home}: No start time, skipping")
                    continue

                try:
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    time_diff = (start_time - now).total_seconds() / 3600  # hours

                    if game_time_filter == "Upcoming Only":
                        if start_time > now:
                            filtered_games.append(game)
                            print(f"  ✓ {away} @ {home}: {start_time} (in {time_diff:.1f}h) - INCLUDED")
                        else:
                            print(f"  ✗ {away} @ {home}: {start_time} ({time_diff:.1f}h ago) - EXCLUDED")
                    elif game_time_filter == "Include Started Games":
                        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                        if start_time >= today_start:
                            filtered_games.append(game)
                            print(f"  ✓ {away} @ {home}: {start_time} - INCLUDED")
                        else:
                            print(f"  ✗ {away} @ {home}: {start_time} - EXCLUDED")
                except Exception as e:
                    print(f"  ⚠ {away} @ {home}: Could not parse time '{start_time_str}': {e}")
                    filtered_games.append(game)

            games = filtered_games
            print(f"\nAfter time filtering ({game_time_filter}): {len(games)} games remaining")

        if not games:
            print("No games match the time filter")
            return pd.DataFrame()

        if max_games:
            games = games[:max_games]

        print(f"Will fetch props for {len(games)} games")

        all_props = []
        for i, game in enumerate(games, 1):
            event_id = game.get("eventId") or game.get("id")
            home = game.get("homeTeam", {}).get("name", "") if isinstance(game.get("homeTeam"), dict) else game.get("home_team", "")
            away = game.get("awayTeam", {}).get("name", "") if isinstance(game.get("awayTeam"), dict) else game.get("away_team", "")

            print(f"[{i}/{len(games)}] Fetching props for {away} @ {home}...")

            try:
                props = self.get_props_for_event(event_id)
                if not props.empty:
                    all_props.append(props)
                    print(f"  ✓ Got {len(props)} props")
                else:
                    print(f"  ⚠ No props available")

            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                continue

        if all_props:
            combined = pd.concat(all_props, ignore_index=True)
            print(f"\n✓ Total props fetched: {len(combined)}")
            return combined
        else:
            print("\n⚠ No props fetched")
            return pd.DataFrame()


def fetch_current_props_from_sportgameodds(
    sport: str = "NFL",
    week: Optional[int] = None,
    season: Optional[int] = None,
    max_games: Optional[int] = None,
    game_time_filter: str = "Upcoming Only",
    api_key: Optional[str] = None
) -> pd.DataFrame:
    """
    Convenience function to fetch current props using SportsGameOdds API.

    Args:
        sport: Sport key (NFL, NBA, MLB)
        week: NFL week (ignored, uses upcoming games)
        season: NFL season (ignored, uses current season)
        max_games: Limit number of games to conserve API requests
        game_time_filter: Filter games by time
        api_key: SportsGameOdds API key (optional, reads from env)

    Returns:
        DataFrame compatible with the analyzer's expected format
    """
    client = SportGameOddsClient(api_key=api_key)
    props = client.fetch_all_current_props(sport=sport, max_games=max_games, game_time_filter=game_time_filter)

    if props.empty:
        return props

    # Add missing columns expected by the analyzer
    if 'team' not in props.columns:
        props['team'] = None

    if 'position' not in props.columns:
        def infer_position(prop_type):
            if 'passing' in prop_type:
                return 'QB'
            elif 'rushing' in prop_type:
                return 'RB'
            elif 'receiving' in prop_type or 'receptions' in prop_type:
                return 'WR/TE'
            elif 'kicking' in prop_type or 'field_goal' in prop_type:
                return 'K'
            elif 'touchdown' in prop_type:
                return 'TD (Any)'
            return 'Unknown'

        props['position'] = props['prop_type'].apply(infer_position)

    if 'opponent' not in props.columns:
        props['opponent'] = None

    return props


def test_sportgameodds_connection(api_key: Optional[str] = None) -> dict:
    """
    Test SportsGameOdds API connection and return status.

    Args:
        api_key: API key to test

    Returns:
        dict with 'valid', 'message', 'details'
    """
    try:
        client = SportGameOddsClient(api_key=api_key)
        games = client.get_upcoming_games(sport="NFL")

        return {
            "valid": True,
            "message": f"✓ Connected! Found {len(games)} upcoming games",
            "details": {
                "games_count": len(games),
                "api_status": "active"
            }
        }

    except ValueError as e:
        return {
            "valid": False,
            "message": str(e),
            "details": {}
        }

    except Exception as e:
        return {
            "valid": False,
            "message": f"Connection failed: {str(e)}",
            "details": {}
        }
