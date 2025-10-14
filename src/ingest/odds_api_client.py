"""
The Odds API client for fetching real betting props across NFL, NBA, and MLB.

API Documentation: https://the-odds-api.com/liveapi/guides/v4/
"""

from typing import Dict, List, Optional
import pandas as pd
import httpx
import time
from pathlib import Path
from datetime import datetime, timedelta
import os

from .sport_config import (
    get_sport_key,
    get_prop_markets,
    normalize_prop_type,
    infer_position,
    get_sport_display_name
)

# Rate limiting
RATE_LIMIT_DELAY = 1.0  # seconds between requests


class OddsAPIClient:
    """
    Client for The Odds API to fetch player props across NFL, NBA, and MLB.

    Free tier: 500 requests/month
    Pricing: https://the-odds-api.com/liveapi/guides/v4/#overview
    """

    BASE_URL = "https://api.the-odds-api.com/v4"

    # Bookmakers to query (DraftKings, FanDuel, BetMGM are most reliable)
    BOOKMAKERS = "draftkings,fanduel,betmgm"

    def __init__(self, api_key: Optional[str] = None, sport: str = "NFL"):
        """
        Initialize The Odds API client.

        Args:
            api_key: API key from the-odds-api.com (or from env var ODDS_API_KEY)
            sport: Sport to fetch props for ("NFL", "NBA", or "MLB")
        """
        self.api_key = api_key or os.getenv("ODDS_API_KEY")
        if not self.api_key:
            raise ValueError("ODDS_API_KEY not found in environment or passed as argument")

        self.sport = sport
        self.sport_key = get_sport_key(sport)
        self.prop_markets = get_prop_markets(sport)

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
        # Create a hash of the endpoint and params to avoid filename length issues
        cache_string = f"{endpoint}_{'_'.join(f'{k}={v}' for k, v in sorted(params.items()))}"
        cache_hash = hashlib.md5(cache_string.encode()).hexdigest()
        return self.cache_dir / f"odds_api_{cache_hash}.parquet"

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

    def _make_request(self, endpoint: str, params: dict) -> dict:
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
        params["apiKey"] = self.api_key

        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()

            # Log remaining requests
            remaining = response.headers.get("x-requests-remaining")
            used = response.headers.get("x-requests-used")
            if remaining and used:
                print(f"API Usage: {used} used, {remaining} remaining this month")

            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid API key. Get one at https://the-odds-api.com/")
            elif e.response.status_code == 429:
                raise ValueError("Rate limit exceeded. Upgrade your plan or wait.")
            else:
                raise ValueError(f"API error: {e.response.status_code} - {e.response.text}")

        except Exception as e:
            raise ValueError(f"Request failed: {str(e)}")

    def get_upcoming_games(self) -> List[Dict]:
        """
        Get list of upcoming games for the selected sport.

        Returns:
            List of game dictionaries with event IDs
        """
        endpoint = f"sports/{self.sport_key}/events"
        params = {}

        cache_path = self._get_cache_path(endpoint, params)

        # Try cache first (1 hour TTL)
        cached = self._load_from_cache(cache_path, ttl_hours=1)
        if cached is not None:
            return cached.to_dict('records')

        # Fetch from API
        data = self._make_request(endpoint, params)

        # Convert to DataFrame for caching
        if data:
            df = pd.DataFrame(data)
            self._save_to_cache(df, cache_path)
            return data

        return []

    def get_props_for_event(
        self,
        event_id: str,
        markets: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Get player props for a specific game using the event-specific endpoint.

        This uses the more efficient /events/{eventId}/odds endpoint which:
        - Returns data for a single event
        - Properly includes player names in the 'description' field
        - Has last_update at the market level (more accurate)

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
        if markets is None:
            markets = self.prop_markets

        endpoint = f"sports/{self.sport_key}/events/{event_id}/odds"
        params = {
            "regions": "us",
            "markets": ",".join(markets),
            "bookmakers": self.BOOKMAKERS,
            "oddsFormat": "american"
        }

        cache_path = self._get_cache_path(endpoint, params)

        # Try cache first (30 min TTL for live odds)
        cached = self._load_from_cache(cache_path, ttl_hours=0.5)
        if cached is not None:
            return cached

        # Fetch from API
        try:
            data = self._make_request(endpoint, params)
        except ValueError as e:
            # Handle 404s gracefully (event may not have props yet)
            if "404" in str(e):
                print(f"  ⚠ No odds available for event {event_id} yet")
                return pd.DataFrame()
            raise

        # Parse response into props DataFrame
        props = self._parse_props_response_v2(data, event_id)

        # Cache results
        if not props.empty:
            self._save_to_cache(props, cache_path)

        return props

    def _parse_props_response(self, data: dict, event_id: str) -> pd.DataFrame:
        """
        Parse The Odds API response into our standard prop format.

        The Odds API format:
        {
            "id": "event_id",
            "sport_key": "americanfootball_nfl",
            "commence_time": "2024-10-13T17:00:00Z",
            "home_team": "Kansas City Chiefs",
            "away_team": "Denver Broncos",
            "bookmakers": [
                {
                    "key": "draftkings",
                    "markets": [
                        {
                            "key": "player_pass_yds",
                            "outcomes": [
                                {
                                    "name": "Patrick Mahomes",
                                    "description": "Over",
                                    "price": -110,
                                    "point": 275.5
                                },
                                {
                                    "name": "Patrick Mahomes",
                                    "description": "Under",
                                    "price": -110,
                                    "point": 275.5
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        """
        props_list = []

        game_time = data.get("commence_time")
        home_team = data.get("home_team")
        away_team = data.get("away_team")

        for bookmaker in data.get("bookmakers", []):
            bookmaker_name = bookmaker.get("key")

            for market in bookmaker.get("markets", []):
                market_key = market.get("key")
                prop_type = normalize_prop_type(market_key, self.sport)

                outcomes = market.get("outcomes", [])

                # Group outcomes by player and point
                player_props = {}
                for outcome in outcomes:
                    player = outcome.get("name")
                    line = outcome.get("point")
                    direction = outcome.get("description", "").lower()
                    price = outcome.get("price")

                    key = (player, line)
                    if key not in player_props:
                        player_props[key] = {}

                    if direction == "over":
                        player_props[key]["over_odds"] = price
                    elif direction == "under":
                        player_props[key]["under_odds"] = price

                # Create prop rows
                for (player, line), odds in player_props.items():
                    # Only include if we have both over and under
                    if "over_odds" in odds and "under_odds" in odds:
                        # Generate player_id from normalized name
                        player_id = player.lower().replace(" ", "_").replace(".", "")

                        # Infer position from prop_type
                        position = infer_position(prop_type, self.sport)

                        props_list.append({
                            "player_id": player_id,
                            "player_name": player,
                            "prop_type": prop_type,
                            "line": line,
                            "over_odds": odds["over_odds"],
                            "under_odds": odds["under_odds"],
                            "bookmaker": bookmaker_name,
                            "game_id": event_id,
                            "game_time": pd.to_datetime(game_time) if game_time else None,
                            "home_team": home_team,
                            "away_team": away_team,
                            "team": None,  # Would need roster data to determine
                            "position": position,
                            "opponent": None,  # Would need to determine which team player is on
                        })

        return pd.DataFrame(props_list) if props_list else pd.DataFrame()

    def _parse_props_response_v2(self, data: dict, event_id: str) -> pd.DataFrame:
        """
        Parse The Odds API event-specific endpoint response.

        This handles the improved format from /events/{eventId}/odds which includes:
        - Player names in the 'description' field of outcomes
        - Market-level last_update timestamps
        - Better structured player prop data

        Example response structure from docs:
        {
            "id": "event_id",
            "home_team": "Team A",
            "away_team": "Team B",
            "commence_time": "2023-01-01T18:00:00Z",
            "bookmakers": [
                {
                    "key": "draftkings",
                    "markets": [
                        {
                            "key": "player_pass_tds",
                            "last_update": "2023-01-01T05:31:29Z",
                            "outcomes": [
                                {
                                    "name": "Over",
                                    "description": "Patrick Mahomes",
                                    "price": -110,
                                    "point": 1.5
                                },
                                ...
                            ]
                        }
                    ]
                }
            ]
        }
        """
        props_list = []

        game_time = data.get("commence_time")
        home_team = data.get("home_team")
        away_team = data.get("away_team")

        for bookmaker in data.get("bookmakers", []):
            bookmaker_name = bookmaker.get("key")

            for market in bookmaker.get("markets", []):
                market_key = market.get("key")
                prop_type = normalize_prop_type(market_key, self.sport)
                last_update = market.get("last_update")  # Now at market level

                outcomes = market.get("outcomes", [])

                # Group outcomes by player (description field) and point
                player_props = {}
                for outcome in outcomes:
                    # For player props, the player name is in 'description'
                    player = outcome.get("description", outcome.get("name"))
                    line = outcome.get("point")
                    direction = outcome.get("name", "").lower()
                    price = outcome.get("price")

                    # Skip if missing key fields
                    if not player or line is None:
                        continue

                    key = (player, line)
                    if key not in player_props:
                        player_props[key] = {}

                    if direction == "over":
                        player_props[key]["over_odds"] = price
                    elif direction == "under":
                        player_props[key]["under_odds"] = price

                # Create prop rows
                for (player, line), odds in player_props.items():
                    # Only include if we have both over and under
                    if "over_odds" in odds and "under_odds" in odds:
                        # Generate player_id from normalized name
                        player_id = player.lower().replace(" ", "_").replace(".", "")

                        # Infer position from prop_type
                        position = infer_position(prop_type, self.sport)

                        props_list.append({
                            "player_id": player_id,
                            "player_name": player,
                            "prop_type": prop_type,
                            "line": line,
                            "over_odds": odds["over_odds"],
                            "under_odds": odds["under_odds"],
                            "bookmaker": bookmaker_name,
                            "game_id": event_id,
                            "game_time": pd.to_datetime(game_time) if game_time else None,
                            "home_team": home_team,
                            "away_team": away_team,
                            "last_update": pd.to_datetime(last_update) if last_update else None,
                            "team": None,  # Would need roster data to determine
                            "position": position,
                            "opponent": None,  # Would need to determine which team player is on
                        })

        return pd.DataFrame(props_list) if props_list else pd.DataFrame()


    def fetch_all_current_props(
        self,
        max_games: Optional[int] = None,
        game_time_filter: str = "Upcoming Only"
    ) -> pd.DataFrame:
        """
        Fetch props for all upcoming games for the selected sport.

        Args:
            max_games: Limit number of games to fetch (to conserve API requests)
            game_time_filter: Filter games by start time
                - "Upcoming Only": Only games that haven't started yet
                - "Include Started Games": Games that started today or later
                - "All Games": All games including past ones

        Returns:
            DataFrame with all props from all upcoming games
        """
        sport_display = get_sport_display_name(self.sport_key)
        print(f"Fetching upcoming {sport_display} games...")
        games = self.get_upcoming_games()

        if not games:
            print("No upcoming games found")
            return pd.DataFrame()

        # Filter games by time to save API credits
        if game_time_filter != "All Games":
            from datetime import timezone
            now = datetime.now(timezone.utc)
            print(f"\nCurrent time (UTC): {now}")
            print(f"Time filter mode: {game_time_filter}")

            filtered_games = []
            for game in games:
                commence_time_str = game.get("commence_time")
                home = game.get("home_team", "Unknown")
                away = game.get("away_team", "Unknown")

                if not commence_time_str:
                    print(f"  ⚠ {away} @ {home}: No commence_time, skipping")
                    continue

                try:
                    # Parse ISO 8601 timestamp
                    commence_time = datetime.fromisoformat(commence_time_str.replace('Z', '+00:00'))
                    time_diff = (commence_time - now).total_seconds() / 3600  # hours

                    if game_time_filter == "Upcoming Only":
                        # Only include games that haven't started yet
                        if commence_time > now:
                            filtered_games.append(game)
                            print(f"  ✓ {away} @ {home}: {commence_time} (in {time_diff:.1f}h) - INCLUDED")
                        else:
                            print(f"  ✗ {away} @ {home}: {commence_time} ({time_diff:.1f}h ago) - EXCLUDED (already started)")
                    elif game_time_filter == "Include Started Games":
                        # Include games from today onwards
                        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                        if commence_time >= today_start:
                            filtered_games.append(game)
                            print(f"  ✓ {away} @ {home}: {commence_time} - INCLUDED (today or later)")
                        else:
                            print(f"  ✗ {away} @ {home}: {commence_time} - EXCLUDED (before today)")
                except Exception as e:
                    print(f"  ⚠ {away} @ {home}: Could not parse time '{commence_time_str}': {e}")
                    filtered_games.append(game)  # Include game if we can't parse time

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
            event_id = game.get("id")
            home = game.get("home_team", "")
            away = game.get("away_team", "")

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


def fetch_current_props_from_odds_api(
    week: Optional[int] = None,
    season: Optional[int] = None,
    max_games: Optional[int] = None,
    game_time_filter: str = "Upcoming Only",
    api_key: Optional[str] = None,
    sport: str = "NFL"
) -> pd.DataFrame:
    """
    Convenience function to fetch current props using The Odds API.

    Args:
        week: NFL week (ignored for now, uses upcoming games)
        season: Season year (ignored for now, uses current season)
        max_games: Limit number of games to conserve API requests
        game_time_filter: Filter games by time ("Upcoming Only", "Include Started Games", "All Games")
        api_key: The Odds API key (optional, reads from env)
        sport: Sport to fetch props for ("NFL", "NBA", or "MLB")

    Returns:
        DataFrame compatible with the analyzer's expected format
    """
    client = OddsAPIClient(api_key=api_key, sport=sport)
    props = client.fetch_all_current_props(max_games=max_games, game_time_filter=game_time_filter)

    if props.empty:
        return props

    # Add missing columns expected by the analyzer
    if 'team' not in props.columns:
        # Try to infer team from player name or use home/away
        props['team'] = None  # Would need roster data to map players to teams

    if 'position' not in props.columns:
        # Infer position from prop type
        def infer_position(prop_type):
            if 'passing' in prop_type:
                return 'QB'
            elif 'rushing' in prop_type or 'rush' in prop_type:
                return 'RB'
            elif 'receiving' in prop_type or 'reception' in prop_type:
                return 'WR/TE'  # Could be WR, TE, or RB
            elif 'kicking' in prop_type or 'field_goal' in prop_type or 'fg_' in prop_type:
                return 'K'
            elif 'touchdown' in prop_type:
                return 'TD (Any)'
            return 'Unknown'

        props['position'] = props['prop_type'].apply(infer_position)

    if 'opponent' not in props.columns:
        props['opponent'] = None  # Would need to determine which team player is on

    return props


def test_odds_api_connection(api_key: Optional[str] = None, sport: str = "NFL") -> dict:
    """
    Test The Odds API connection and return status.

    Args:
        api_key: API key to test
        sport: Sport to test ("NFL", "NBA", or "MLB")

    Returns:
        dict with 'valid', 'message', 'details'
    """
    try:
        client = OddsAPIClient(api_key=api_key, sport=sport)
        games = client.get_upcoming_games()

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
