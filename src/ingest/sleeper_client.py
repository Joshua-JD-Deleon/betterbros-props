"""
Sleeper API client for fetching player props.

ToS Compliance:
- Respects Sleeper API rate limits (documented at api.sleeper.app)
- Uses official API endpoints only
- Implements exponential backoff for retries
- Caches responses to minimize API calls
"""

from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from pathlib import Path
import httpx
import pandas as pd
import time
import logging
import random
import os

logger = logging.getLogger(__name__)


class SleeperClient:
    """
    Client for interacting with Sleeper API.

    Includes mock mode for development/testing without API calls.
    """

    BASE_URL = "https://api.sleeper.app/v1"
    RATE_LIMIT_DELAY = 1.0  # Seconds between requests
    MAX_RETRIES = 3
    CACHE_DURATION_HOURS = 1

    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = True, cache_dir: Optional[Path] = None, sport: str = "NFL"):
        """
        Initialize Sleeper API client.

        Args:
            api_key: API key for authentication (if required)
            mock_mode: If True, return mock data instead of making API calls
            cache_dir: Directory for caching API responses
            sport: Sport to fetch data for ("NFL", "NBA", or "MLB")
        """
        self.api_key = api_key or os.getenv("SLEEPER_API_KEY")
        self.mock_mode = mock_mode
        self.sport = sport
        self.last_request_time = 0.0
        self.cache_dir = cache_dir or Path("./data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _rate_limit(self) -> None:
        """Implement rate limiting between requests (1 req/sec)."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()

    def _get_cache_path(self, week: int, season: int) -> Path:
        """Get cache file path for given week/season/sport."""
        return self.cache_dir / f"sleeper_{self.sport}_{week}_{season}.parquet"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file exists and is within duration limit."""
        if not cache_path.exists():
            return False

        file_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        return file_age < timedelta(hours=self.CACHE_DURATION_HOURS)

    def _get_mock_props(self, week: int, season: int) -> pd.DataFrame:
        """
        Generate realistic mock props data for development that varies by week.

        Args:
            week: NFL week number (1-18) - used to vary data
            season: Season year - used in seed

        Returns:
            DataFrame with 20-30 mock player props that vary realistically by week
        """
        # Use week and season as seed for deterministic but varied data
        random.seed(week * 1000 + season)

        # Base player data with baseline stats
        players = [
            # (player_id, name, team, position, base_pass_yds, base_pass_tds, base_rush_yds, base_rec_yds, base_rec, base_fg_made, base_kicking_pts)
            ("player_001", "Patrick Mahomes", "KC", "QB", 275.0, 2.0, None, None, None, None, None),
            ("player_002", "Josh Allen", "BUF", "QB", 265.0, 2.0, None, None, None, None, None),
            ("player_003", "Lamar Jackson", "BAL", "QB", 240.0, 1.5, None, None, None, None, None),
            ("player_004", "Jalen Hurts", "PHI", "QB", 250.0, 2.0, None, None, None, None, None),
            ("player_005", "Joe Burrow", "CIN", "QB", 270.0, 2.0, None, None, None, None, None),
            # WRs
            ("player_006", "Tyreek Hill", "MIA", "WR", None, None, None, 85.0, 6.5, None, None),
            ("player_007", "Stefon Diggs", "BUF", "WR", None, None, None, 75.0, 6.0, None, None),
            ("player_008", "Justin Jefferson", "MIN", "WR", None, None, None, 90.0, 7.0, None, None),
            ("player_009", "CeeDee Lamb", "DAL", "WR", None, None, None, 80.0, 6.5, None, None),
            ("player_010", "Ja'Marr Chase", "CIN", "WR", None, None, None, 82.0, 6.0, None, None),
            # TEs
            ("player_011", "Travis Kelce", "KC", "TE", None, None, None, 68.0, 5.5, None, None),
            ("player_012", "Mark Andrews", "BAL", "TE", None, None, None, 62.0, 5.0, None, None),
            ("player_013", "George Kittle", "SF", "TE", None, None, None, 65.0, 5.0, None, None),
            # RBs
            ("player_014", "Christian McCaffrey", "SF", "RB", None, None, 85.0, None, None, None, None),
            ("player_015", "Derrick Henry", "TEN", "RB", None, None, 95.0, None, None, None, None),
            ("player_016", "Saquon Barkley", "NYG", "RB", None, None, 78.0, None, None, None, None),
            # Kickers
            ("player_017", "Justin Tucker", "BAL", "K", None, None, None, None, None, 2.5, 9.5),
            ("player_018", "Harrison Butker", "KC", "K", None, None, None, None, None, 2.0, 9.0),
            ("player_019", "Jake Moody", "SF", "K", None, None, None, None, None, 2.0, 8.5),
        ]

        # Pool of all NFL teams for opponent rotation
        all_teams = ["KC", "BUF", "BAL", "PHI", "CIN", "MIA", "MIN", "DAL", "SF", "NYG",
                     "LV", "NYJ", "CLE", "NE", "GB", "SEA", "LAR", "DEN", "IND", "TEN",
                     "WAS", "TB", "NO", "ATL", "CAR", "ARI", "LAC", "JAX", "HOU", "PIT", "DET", "CHI"]

        # Player injury status varies by week (some players out certain weeks)
        injured_weeks = {
            "player_006": [3],  # Tyreek Hill out week 3
            "player_015": [5, 6],  # Derrick Henry out weeks 5-6
            "player_012": [2],  # Mark Andrews out week 2
        }

        props_data = []
        game_id_counter = 1

        # Generate props for each player
        for player_data in players:
            player_id, player_name, team, position = player_data[0], player_data[1], player_data[2], player_data[3]
            base_pass, base_td, base_rush, base_rec_yds, base_rec = player_data[4:9]
            base_fg_made, base_kicking_pts = player_data[9:11] if len(player_data) >= 11 else (None, None)
            # Skip if player is injured this week
            if player_id in injured_weeks and week in injured_weeks[player_id]:
                continue

            # Rotate opponent based on week (deterministic)
            available_opponents = [t for t in all_teams if t != team]
            opponent = available_opponents[(week + hash(player_id)) % len(available_opponents)]

            game_id = f"game_{week:02d}_{game_id_counter:03d}"

            # Game time varies by week (Sunday 1pm, 4pm, Sunday night, Monday night)
            week_start = datetime(season, 9, 7) + timedelta(weeks=week-1)
            game_slot = (week + hash(player_id)) % 4
            if game_slot == 0:
                game_time = week_start + timedelta(days=0, hours=13)  # Sunday 1pm
            elif game_slot == 1:
                game_time = week_start + timedelta(days=0, hours=16)  # Sunday 4pm
            elif game_slot == 2:
                game_time = week_start + timedelta(days=0, hours=20)  # Sunday night
            else:
                game_time = week_start + timedelta(days=1, hours=20)  # Monday night

            home_away = "home" if (week + hash(player_id)) % 2 == 0 else "away"

            # Week-based form modifier (-15% to +15%)
            form_modifier = 1.0 + ((week % 7) - 3) * 0.05  # Creates realistic week-to-week variation

            # Generate position-specific props with week-based variation
            if position == "QB" and base_pass is not None:
                # Passing yards - varies by week and form
                passing_line = base_pass * form_modifier
                props_data.append({
                    "player_id": player_id,
                    "player_name": player_name,
                    "team": team,
                    "position": position,
                    "opponent": opponent,
                    "prop_type": "passing_yards",
                    "line": passing_line,
                    "over_odds": random.choice([-110, -115, -105, -120, -108]),
                    "under_odds": random.choice([-110, -105, -115, -100, -112]),
                    "game_id": game_id,
                    "game_time": game_time,
                    "home_away": home_away,
                })
                # Passing TDs - varies by week
                td_line = base_td * form_modifier
                props_data.append({
                    "player_id": player_id,
                    "player_name": player_name,
                    "team": team,
                    "position": position,
                    "opponent": opponent,
                    "prop_type": "passing_tds",
                    "line": td_line,
                    "over_odds": random.choice([-110, -115, -105, -120]),
                    "under_odds": random.choice([-110, -105, -115, -100]),
                    "game_id": game_id,
                    "game_time": game_time,
                    "home_away": home_away,
                })

            elif position == "WR" and base_rec_yds is not None:
                # Receiving yards - varies by week
                rec_yds_line = base_rec_yds * form_modifier
                props_data.append({
                    "player_id": player_id,
                    "player_name": player_name,
                    "team": team,
                    "position": position,
                    "opponent": opponent,
                    "prop_type": "receiving_yards",
                    "line": rec_yds_line,
                    "over_odds": random.choice([-110, -115, -105, -120, -108]),
                    "under_odds": random.choice([-110, -105, -115, -100, -112]),
                    "game_id": game_id,
                    "game_time": game_time,
                    "home_away": home_away,
                })
                # Receptions - varies by week
                rec_line = base_rec * form_modifier
                props_data.append({
                    "player_id": player_id,
                    "player_name": player_name,
                    "team": team,
                    "position": position,
                    "opponent": opponent,
                    "prop_type": "receptions",
                    "line": rec_line,
                    "over_odds": random.choice([-110, -115, -105, -120]),
                    "under_odds": random.choice([-110, -105, -115, -100]),
                    "game_id": game_id,
                    "game_time": game_time,
                    "home_away": home_away,
                })

            elif position == "TE" and base_rec_yds is not None:
                # Receiving yards - varies by week
                rec_yds_line = base_rec_yds * form_modifier
                props_data.append({
                    "player_id": player_id,
                    "player_name": player_name,
                    "team": team,
                    "position": position,
                    "opponent": opponent,
                    "prop_type": "receiving_yards",
                    "line": rec_yds_line,
                    "over_odds": random.choice([-110, -115, -105, -120]),
                    "under_odds": random.choice([-110, -105, -115, -100]),
                    "game_id": game_id,
                    "game_time": game_time,
                    "home_away": home_away,
                })
                # Receptions - varies by week
                rec_line = base_rec * form_modifier
                props_data.append({
                    "player_id": player_id,
                    "player_name": player_name,
                    "team": team,
                    "position": position,
                    "opponent": opponent,
                    "prop_type": "receptions",
                    "line": rec_line,
                    "over_odds": random.choice([-110, -115, -105]),
                    "under_odds": random.choice([-110, -105, -115]),
                    "game_id": game_id,
                    "game_time": game_time,
                    "home_away": home_away,
                })

            elif position == "RB" and base_rush is not None:
                # Rushing yards - varies by week
                rush_line = base_rush * form_modifier
                props_data.append({
                    "player_id": player_id,
                    "player_name": player_name,
                    "team": team,
                    "position": position,
                    "opponent": opponent,
                    "prop_type": "rushing_yards",
                    "line": rush_line,
                    "over_odds": random.choice([-110, -115, -105, -120]),
                    "under_odds": random.choice([-110, -105, -115, -100]),
                    "game_id": game_id,
                    "game_time": game_time,
                    "home_away": home_away,
                })

            elif position == "K" and base_fg_made is not None:
                # Field goals made - varies by week
                fg_line = base_fg_made * form_modifier
                props_data.append({
                    "player_id": player_id,
                    "player_name": player_name,
                    "team": team,
                    "position": position,
                    "opponent": opponent,
                    "prop_type": "field_goals_made",
                    "line": fg_line,
                    "over_odds": random.choice([-110, -115, -105, -120]),
                    "under_odds": random.choice([-110, -105, -115, -100]),
                    "game_id": game_id,
                    "game_time": game_time,
                    "home_away": home_away,
                })
                # Kicking points - varies by week
                if base_kicking_pts is not None:
                    kicking_pts_line = base_kicking_pts * form_modifier
                    props_data.append({
                        "player_id": player_id,
                        "player_name": player_name,
                        "team": team,
                        "position": position,
                        "opponent": opponent,
                        "prop_type": "kicking_points",
                        "line": kicking_pts_line,
                        "over_odds": random.choice([-110, -115, -105]),
                        "under_odds": random.choice([-110, -105, -115]),
                        "game_id": game_id,
                        "game_time": game_time,
                        "home_away": home_away,
                    })

            game_id_counter += 1

        df = pd.DataFrame(props_data)

        # Round line values to nearest 0.5
        df['line'] = (df['line'] * 2).round() / 2

        # Reset random seed to not affect other parts of the code
        random.seed()

        return df

    def _get_mock_props_nba(self, game_date: datetime, season: int) -> pd.DataFrame:
        """
        Generate realistic NBA mock props data for development.

        Args:
            game_date: Date for which to generate props
            season: Season year

        Returns:
            DataFrame with NBA player props
        """
        # Use date as seed for deterministic but varied data
        random.seed(game_date.toordinal() + season)

        # Base player data for NBA stars
        players = [
            # (player_id, name, team, position, points, rebounds, assists, threes, blocks, steals)
            ("nba_001", "Luka Dončić", "DAL", "PG", 32.0, 8.5, 9.0, 3.5, 0.5, 1.5),
            ("nba_002", "Giannis Antetokounmpo", "MIL", "PF", 31.0, 11.5, 5.5, 1.0, 1.5, 1.0),
            ("nba_003", "Joel Embiid", "PHI", "C", 33.0, 10.5, 4.5, 1.5, 1.5, 1.0),
            ("nba_004", "Nikola Jokić", "DEN", "C", 26.5, 12.0, 9.0, 1.0, 0.8, 1.3),
            ("nba_005", "Stephen Curry", "GSW", "PG", 28.0, 5.0, 6.5, 5.0, 0.3, 1.0),
            ("nba_006", "Jayson Tatum", "BOS", "SF", 27.0, 8.5, 4.5, 3.0, 0.7, 1.0),
            ("nba_007", "Kevin Durant", "PHX", "SF", 29.0, 6.5, 5.0, 2.0, 1.3, 0.8),
            ("nba_008", "LeBron James", "LAL", "SF", 25.0, 7.5, 7.5, 2.5, 0.6, 1.3),
            ("nba_009", "Damian Lillard", "MIL", "PG", 26.0, 4.5, 7.0, 4.0, 0.3, 0.9),
            ("nba_010", "Anthony Davis", "LAL", "PF", 24.0, 12.0, 3.5, 0.5, 2.3, 1.2),
            ("nba_011", "Donovan Mitchell", "CLE", "SG", 28.0, 5.0, 5.5, 3.5, 0.4, 1.5),
            ("nba_012", "Shai Gilgeous-Alexander", "OKC", "PG", 31.0, 5.5, 6.0, 2.0, 0.9, 2.0),
            ("nba_013", "Devin Booker", "PHX", "SG", 27.0, 4.5, 6.5, 3.0, 0.5, 0.8),
            ("nba_014", "Jaylen Brown", "BOS", "SG", 26.0, 6.5, 3.5, 2.5, 0.5, 1.2),
            ("nba_015", "Anthony Edwards", "MIN", "SG", 25.0, 5.5, 5.0, 3.0, 0.6, 1.5),
        ]

        # Pool of NBA teams
        all_teams = ["LAL", "GSW", "BOS", "PHX", "MIL", "DAL", "PHI", "DEN", "MIA", "CLE",
                     "NYK", "BKN", "MEM", "SAC", "MIN", "NOP", "OKC", "ATL", "CHI", "TOR",
                     "IND", "ORL", "WAS", "CHA", "POR", "UTA", "SAS", "HOU", "DET", "LAC"]

        props_data = []
        game_id_counter = 1

        # Generate props for each player
        for player_data in players:
            player_id, player_name, team, position = player_data[:4]
            base_points, base_rebounds, base_assists, base_threes, base_blocks, base_steals = player_data[4:10]

            # Rotate opponent based on date
            available_opponents = [t for t in all_teams if t != team]
            opponent = available_opponents[(game_date.toordinal() + hash(player_id)) % len(available_opponents)]

            game_id = f"nba_game_{game_date.strftime('%Y%m%d')}_{game_id_counter:03d}"

            # Game times vary (7pm, 7:30pm, 8pm, 10pm ET)
            time_slot = (game_date.toordinal() + hash(player_id)) % 4
            hour_offset = [19, 19.5, 20, 22][time_slot]
            game_time = game_date.replace(hour=int(hour_offset), minute=int((hour_offset % 1) * 60))

            home_away = "home" if (game_date.toordinal() + hash(player_id)) % 2 == 0 else "away"

            # Form modifier for realistic variation
            form_modifier = 1.0 + ((game_date.toordinal() % 7) - 3) * 0.05

            # Points prop
            points_line = base_points * form_modifier
            props_data.append({
                "player_id": player_id,
                "player_name": player_name,
                "team": team,
                "position": position,
                "opponent": opponent,
                "prop_type": "points",
                "line": points_line,
                "over_odds": random.choice([-110, -115, -105, -120, -108]),
                "under_odds": random.choice([-110, -105, -115, -100, -112]),
                "game_id": game_id,
                "game_time": game_time,
                "home_away": home_away,
            })

            # Rebounds prop
            rebounds_line = base_rebounds * form_modifier
            props_data.append({
                "player_id": player_id,
                "player_name": player_name,
                "team": team,
                "position": position,
                "opponent": opponent,
                "prop_type": "rebounds",
                "line": rebounds_line,
                "over_odds": random.choice([-110, -115, -105, -120]),
                "under_odds": random.choice([-110, -105, -115, -100]),
                "game_id": game_id,
                "game_time": game_time,
                "home_away": home_away,
            })

            # Assists prop
            assists_line = base_assists * form_modifier
            props_data.append({
                "player_id": player_id,
                "player_name": player_name,
                "team": team,
                "position": position,
                "opponent": opponent,
                "prop_type": "assists",
                "line": assists_line,
                "over_odds": random.choice([-110, -115, -105, -120]),
                "under_odds": random.choice([-110, -105, -115, -100]),
                "game_id": game_id,
                "game_time": game_time,
                "home_away": home_away,
            })

            # Three-pointers made
            threes_line = base_threes * form_modifier
            props_data.append({
                "player_id": player_id,
                "player_name": player_name,
                "team": team,
                "position": position,
                "opponent": opponent,
                "prop_type": "three_pointers_made",
                "line": threes_line,
                "over_odds": random.choice([-110, -115, -105, -120]),
                "under_odds": random.choice([-110, -105, -115, -100]),
                "game_id": game_id,
                "game_time": game_time,
                "home_away": home_away,
            })

            # Points + Rebounds + Assists combo
            pra_line = (base_points + base_rebounds + base_assists) * form_modifier
            props_data.append({
                "player_id": player_id,
                "player_name": player_name,
                "team": team,
                "position": position,
                "opponent": opponent,
                "prop_type": "points_rebounds_assists",
                "line": pra_line,
                "over_odds": random.choice([-110, -115, -105, -120]),
                "under_odds": random.choice([-110, -105, -115, -100]),
                "game_id": game_id,
                "game_time": game_time,
                "home_away": home_away,
            })

            game_id_counter += 1

        df = pd.DataFrame(props_data)

        # Round line values to nearest 0.5
        df['line'] = (df['line'] * 2).round() / 2

        # Reset random seed
        random.seed()

        return df

    def _get_mock_props_mlb(self, game_date: datetime, season: int) -> pd.DataFrame:
        """
        Generate realistic MLB mock props data for development.

        Args:
            game_date: Date for which to generate props
            season: Season year

        Returns:
            DataFrame with MLB player props
        """
        # Use date as seed for deterministic but varied data
        random.seed(game_date.toordinal() + season)

        # Base player data for MLB stars
        players = [
            # Batters: (player_id, name, team, position, hits, home_runs, rbis, runs, stolen_bases, total_bases)
            ("mlb_001", "Shohei Ohtani", "LAD", "DH", 1.5, 0.7, 1.2, 1.0, 0.3, 2.5),
            ("mlb_002", "Aaron Judge", "NYY", "RF", 1.5, 0.8, 1.3, 1.1, 0.1, 2.6),
            ("mlb_003", "Ronald Acuña Jr.", "ATL", "RF", 1.6, 0.6, 1.0, 1.2, 0.5, 2.8),
            ("mlb_004", "Mookie Betts", "LAD", "RF", 1.7, 0.6, 1.1, 1.2, 0.2, 2.7),
            ("mlb_005", "Freddie Freeman", "LAD", "1B", 1.6, 0.5, 1.2, 1.0, 0.2, 2.5),
            ("mlb_006", "Juan Soto", "NYY", "LF", 1.5, 0.6, 1.1, 1.1, 0.1, 2.6),
            ("mlb_007", "Fernando Tatis Jr.", "SD", "RF", 1.5, 0.7, 1.2, 1.1, 0.4, 2.7),
            ("mlb_008", "José Ramírez", "CLE", "3B", 1.6, 0.5, 1.3, 1.0, 0.3, 2.5),
            ("mlb_009", "Mike Trout", "LAA", "CF", 1.5, 0.8, 1.2, 1.1, 0.2, 2.8),
            ("mlb_010", "Bobby Witt Jr.", "KC", "SS", 1.7, 0.5, 1.1, 1.2, 0.6, 2.6),
            # Pitchers: (player_id, name, team, position, strikeouts, hits_allowed, walks, earned_runs, outs_recorded)
            ("mlb_p01", "Gerrit Cole", "NYY", "P", 7.5, 5.5, 2.0, 2.5, 18.0),
            ("mlb_p02", "Spencer Strider", "ATL", "P", 9.0, 4.5, 2.5, 2.0, 18.0),
            ("mlb_p03", "Zack Wheeler", "PHI", "P", 7.0, 5.0, 2.0, 2.5, 19.0),
            ("mlb_p04", "Corbin Burnes", "BAL", "P", 7.5, 5.0, 1.5, 2.0, 19.0),
            ("mlb_p05", "Blake Snell", "SF", "P", 8.0, 5.5, 3.0, 2.5, 17.0),
        ]

        # Pool of MLB teams
        all_teams = ["NYY", "LAD", "HOU", "ATL", "SD", "PHI", "SEA", "TB", "BAL", "TOR",
                     "BOS", "MIN", "CLE", "CHW", "DET", "KC", "TEX", "LAA", "OAK",
                     "NYM", "MIA", "WSH", "STL", "MIL", "CHC", "CIN", "PIT", "SF", "ARI", "COL"]

        props_data = []
        game_id_counter = 1

        # Generate props for each player
        for player_data in players:
            player_id, player_name, team, position = player_data[:4]

            # Rotate opponent based on date
            available_opponents = [t for t in all_teams if t != team]
            opponent = available_opponents[(game_date.toordinal() + hash(player_id)) % len(available_opponents)]

            game_id = f"mlb_game_{game_date.strftime('%Y%m%d')}_{game_id_counter:03d}"

            # MLB game times vary (1pm, 4pm, 7pm, 10pm ET)
            time_slot = (game_date.toordinal() + hash(player_id)) % 4
            hour_offset = [13, 16, 19, 22][time_slot]
            game_time = game_date.replace(hour=hour_offset, minute=10)

            home_away = "home" if (game_date.toordinal() + hash(player_id)) % 2 == 0 else "away"

            # Form modifier for realistic variation
            form_modifier = 1.0 + ((game_date.toordinal() % 7) - 3) * 0.05

            if position != "P":  # Batter props
                hits, home_runs, rbis, runs, stolen_bases, total_bases = player_data[4:10]

                # Hits prop
                hits_line = hits * form_modifier
                props_data.append({
                    "player_id": player_id,
                    "player_name": player_name,
                    "team": team,
                    "position": "BATTER",
                    "opponent": opponent,
                    "prop_type": "hits",
                    "line": hits_line,
                    "over_odds": random.choice([-110, -115, -105, -120]),
                    "under_odds": random.choice([-110, -105, -115, -100]),
                    "game_id": game_id,
                    "game_time": game_time,
                    "home_away": home_away,
                })

                # Home runs prop
                hr_line = home_runs * form_modifier
                props_data.append({
                    "player_id": player_id,
                    "player_name": player_name,
                    "team": team,
                    "position": "BATTER",
                    "opponent": opponent,
                    "prop_type": "home_runs",
                    "line": hr_line,
                    "over_odds": random.choice([-110, -115, -105, -120]),
                    "under_odds": random.choice([-110, -105, -115, -100]),
                    "game_id": game_id,
                    "game_time": game_time,
                    "home_away": home_away,
                })

                # RBIs prop
                rbis_line = rbis * form_modifier
                props_data.append({
                    "player_id": player_id,
                    "player_name": player_name,
                    "team": team,
                    "position": "BATTER",
                    "opponent": opponent,
                    "prop_type": "rbis",
                    "line": rbis_line,
                    "over_odds": random.choice([-110, -115, -105, -120]),
                    "under_odds": random.choice([-110, -105, -115, -100]),
                    "game_id": game_id,
                    "game_time": game_time,
                    "home_away": home_away,
                })

                # Total bases prop
                tb_line = total_bases * form_modifier
                props_data.append({
                    "player_id": player_id,
                    "player_name": player_name,
                    "team": team,
                    "position": "BATTER",
                    "opponent": opponent,
                    "prop_type": "total_bases",
                    "line": tb_line,
                    "over_odds": random.choice([-110, -115, -105, -120]),
                    "under_odds": random.choice([-110, -105, -115, -100]),
                    "game_id": game_id,
                    "game_time": game_time,
                    "home_away": home_away,
                })

            else:  # Pitcher props
                strikeouts, hits_allowed, walks, earned_runs, outs_recorded = player_data[4:9]

                # Strikeouts prop
                k_line = strikeouts * form_modifier
                props_data.append({
                    "player_id": player_id,
                    "player_name": player_name,
                    "team": team,
                    "position": "PITCHER",
                    "opponent": opponent,
                    "prop_type": "pitcher_strikeouts",
                    "line": k_line,
                    "over_odds": random.choice([-110, -115, -105, -120]),
                    "under_odds": random.choice([-110, -105, -115, -100]),
                    "game_id": game_id,
                    "game_time": game_time,
                    "home_away": home_away,
                })

                # Hits allowed prop
                h_line = hits_allowed * form_modifier
                props_data.append({
                    "player_id": player_id,
                    "player_name": player_name,
                    "team": team,
                    "position": "PITCHER",
                    "opponent": opponent,
                    "prop_type": "pitcher_hits_allowed",
                    "line": h_line,
                    "over_odds": random.choice([-110, -115, -105, -120]),
                    "under_odds": random.choice([-110, -105, -115, -100]),
                    "game_id": game_id,
                    "game_time": game_time,
                    "home_away": home_away,
                })

                # Outs recorded prop
                outs_line = outs_recorded * form_modifier
                props_data.append({
                    "player_id": player_id,
                    "player_name": player_name,
                    "team": team,
                    "position": "PITCHER",
                    "opponent": opponent,
                    "prop_type": "pitcher_outs",
                    "line": outs_line,
                    "over_odds": random.choice([-110, -115, -105, -120]),
                    "under_odds": random.choice([-110, -105, -115, -100]),
                    "game_id": game_id,
                    "game_time": game_time,
                    "home_away": home_away,
                })

            game_id_counter += 1

        df = pd.DataFrame(props_data)

        # Round line values to nearest 0.5
        df['line'] = (df['line'] * 2).round() / 2

        # Reset random seed
        random.seed()

        return df

    def _fetch_with_retry(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Fetch data from API with exponential backoff retry logic.

        Args:
            url: API endpoint URL
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            httpx.HTTPError: If all retries fail
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                self._rate_limit()

                with httpx.Client(timeout=30.0) as client:
                    headers = {}
                    if self.api_key:
                        headers["Authorization"] = f"Bearer {self.api_key}"

                    response = client.get(url, params=params, headers=headers)
                    response.raise_for_status()
                    return response.json()

            except httpx.HTTPError as e:
                if attempt == self.MAX_RETRIES - 1:
                    logger.error(f"API request failed after {self.MAX_RETRIES} attempts: {e}")
                    raise

                # Exponential backoff: 2^attempt seconds
                wait_time = 2 ** attempt
                logger.warning(f"API request failed (attempt {attempt + 1}/{self.MAX_RETRIES}), retrying in {wait_time}s: {e}")
                time.sleep(wait_time)

    def fetch_props(
        self,
        week: int,
        season: int,
        prop_types: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Fetch player props for a specific week.

        Args:
            week: NFL week number (1-18)
            season: Season year
            prop_types: List of prop types to fetch (e.g., ['passing_yards', 'rushing_yards'])
                       If None, fetches all available props

        Returns:
            DataFrame with columns:
                - player_id: Unique player identifier
                - player_name: Player full name
                - team: Player's team abbreviation
                - position: Player position
                - opponent: Opponent team abbreviation
                - prop_type: Type of prop (e.g., 'passing_yards')
                - line: Prop line value
                - over_odds: Odds for over (American format)
                - under_odds: Odds for under (American format)
                - game_id: Unique game identifier
                - game_time: Scheduled game time
                - home_away: Whether player is home or away
        """
        # Check cache first
        cache_path = self._get_cache_path(week, season)
        if self._is_cache_valid(cache_path):
            logger.info(f"Loading props from cache: {cache_path}")
            df = pd.read_parquet(cache_path)
            if prop_types:
                df = df[df['prop_type'].isin(prop_types)]
            return df

        if self.mock_mode:
            logger.info(f"Using mock data for {self.sport} props")
            if self.sport == "NFL":
                df = self._get_mock_props(week, season)
            elif self.sport == "NBA":
                # For NBA, use date-based approach instead of week
                game_date = datetime.now() if week is None else datetime(season, 10, 1) + timedelta(days=week*7)
                df = self._get_mock_props_nba(game_date, season)
            elif self.sport == "MLB":
                # For MLB, use date-based approach instead of week
                game_date = datetime.now() if week is None else datetime(season, 4, 1) + timedelta(days=week*7)
                df = self._get_mock_props_mlb(game_date, season)
            else:
                logger.warning(f"Unknown sport {self.sport}, falling back to NFL")
                df = self._get_mock_props(week, season)
        else:
            try:
                logger.info(f"Fetching props from Sleeper API for week {week}, season {season}")
                # Note: Sleeper API doesn't have a direct props endpoint in their public API
                # This would need to be adapted based on actual available endpoints
                # For now, we fall back to mock mode if real API is not available
                url = f"{self.BASE_URL}/stats/nfl/{season}/{week}"
                data = self._fetch_with_retry(url)

                # Transform API response to our format
                # This is a placeholder - actual implementation depends on API response structure
                df = self._get_mock_props(week, season)
                logger.warning("Real API implementation pending - using mock data")

            except Exception as e:
                logger.error(f"Error fetching from Sleeper API: {e}, falling back to mock data")
                df = self._get_mock_props(week, season)

        # Cache the results
        try:
            df.to_parquet(cache_path, index=False)
            logger.info(f"Cached props to {cache_path}")
        except Exception as e:
            logger.warning(f"Failed to cache props: {e}")

        if prop_types:
            df = df[df['prop_type'].isin(prop_types)]

        return df

    def fetch_player_info(self, player_id: str) -> Dict[str, Any]:
        """
        Fetch detailed player information.

        Args:
            player_id: Unique player identifier

        Returns:
            Dictionary with player details (position, team, etc.)
        """
        if self.mock_mode:
            return {
                "player_id": player_id,
                "full_name": "Mock Player",
                "position": "QB",
                "team": "KC",
                "age": 28,
                "years_exp": 5
            }

        try:
            self._rate_limit()
            url = f"{self.BASE_URL}/players/nfl/{player_id}"
            return self._fetch_with_retry(url)
        except Exception as e:
            logger.error(f"Error fetching player info for {player_id}: {e}")
            return {}


def fetch_current_props(
    week: Optional[int] = None,
    season: Optional[int] = None,
    mock_mode: bool = True,
    sport: str = "NFL"
) -> pd.DataFrame:
    """
    Convenience function to fetch current week's props.

    Args:
        week: Week number (NFL-specific, defaults to current week)
        season: Season year (defaults to current season)
        mock_mode: Whether to use mock data
        sport: Sport to fetch props for ("NFL", "NBA", or "MLB")

    Returns:
        DataFrame with player props including:
            - player_name, team, position, opponent
            - prop_type (varies by sport)
            - line (the threshold value)
            - over_odds, under_odds (American odds format, e.g., -110, +100)
            - game_id, game_time
    """
    if week is None:
        # Calculate current week based on season start (approximate)
        today = datetime.now()
        if sport == "NFL":
            season_start = datetime(today.year, 9, 7)  # Approximate NFL season start
            if today >= season_start:
                week = min(((today - season_start).days // 7) + 1, 18)
            else:
                week = 1
        else:
            # For NBA/MLB, week is less relevant but we'll default to 1
            week = 1

    if season is None:
        season = datetime.now().year

    client = SleeperClient(mock_mode=mock_mode, sport=sport)
    return client.fetch_props(week=week, season=season)
