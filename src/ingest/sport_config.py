"""
Sport-specific configuration for props across NFL, NBA, and MLB.
"""

from typing import Dict, List

# Sport keys used by The Odds API
SPORT_KEYS = {
    "NFL": "americanfootball_nfl",
    "NBA": "basketball_nba",
    "MLB": "baseball_mlb"
}

# Sport-specific player prop markets
SPORT_PROP_MARKETS = {
    "NFL": [
        # Passing props
        "player_pass_tds",
        "player_pass_yds",
        "player_pass_completions",
        "player_pass_attempts",
        "player_pass_interceptions",
        # Rushing props
        "player_rush_yds",
        "player_rush_attempts",
        # Receiving props
        "player_receptions",
        "player_reception_yds",
        # TD props
        "player_anytime_td",
        "player_1st_td",
        "player_last_td",
        # Kicker props
        "player_field_goals",
        "player_kicking_points",
    ],
    "NBA": [
        # Scoring props
        "player_points",
        "player_threes",
        # Rebounding props
        "player_rebounds",
        "player_rebounds_offensive",
        "player_rebounds_defensive",
        # Passing props
        "player_assists",
        # Defense props
        "player_blocks",
        "player_steals",
        # Other
        "player_turnovers",
        "player_points_rebounds_assists",
        "player_first_basket",
    ],
    "MLB": [
        # Hitting props
        "player_home_runs",
        "player_hits",
        "player_total_bases",
        "player_rbis",
        "player_runs",
        "player_stolen_bases",
        # Pitching props
        "player_pitcher_strikeouts",
        "player_pitcher_hits_allowed",
        "player_pitcher_walks",
        "player_pitcher_earned_runs",
        "player_pitcher_outs",
    ]
}

# Prop type normalization mappings for each sport
PROP_TYPE_MAPPINGS = {
    "NFL": {
        "pass_tds": "passing_tds",
        "pass_yds": "passing_yards",
        "pass_completions": "passing_completions",
        "pass_attempts": "passing_attempts",
        "pass_interceptions": "passing_interceptions",
        "rush_yds": "rushing_yards",
        "rush_attempts": "rushing_attempts",
        "receptions": "receptions",
        "reception_yds": "receiving_yards",
        "anytime_td": "anytime_touchdown",
        "1st_td": "first_touchdown",
        "first_td": "first_touchdown",
        "last_td": "last_touchdown",
        "field_goals": "field_goals_made",
        "field_goals_made": "field_goals_made",
        "kicking_points": "kicking_points",
    },
    "NBA": {
        "points": "points",
        "threes": "three_pointers_made",
        "rebounds": "rebounds",
        "rebounds_offensive": "offensive_rebounds",
        "rebounds_defensive": "defensive_rebounds",
        "assists": "assists",
        "blocks": "blocks",
        "steals": "steals",
        "turnovers": "turnovers",
        "points_rebounds_assists": "points_rebounds_assists",
        "first_basket": "first_basket",
    },
    "MLB": {
        "home_runs": "home_runs",
        "hits": "hits",
        "total_bases": "total_bases",
        "rbis": "rbis",
        "runs": "runs",
        "stolen_bases": "stolen_bases",
        "pitcher_strikeouts": "pitcher_strikeouts",
        "pitcher_hits_allowed": "pitcher_hits_allowed",
        "pitcher_walks": "pitcher_walks",
        "pitcher_earned_runs": "pitcher_earned_runs",
        "pitcher_outs": "pitcher_outs",
    }
}

# Position inference based on prop types for each sport
POSITION_INFERENCE = {
    "NFL": {
        "passing": "QB",
        "rush": "RB",
        "receiving": "WR/TE",
        "receptions": "WR/TE",
        "kicking": "K",
        "field_goal": "K",
        "touchdown": "FLEX"
    },
    "NBA": {
        "points": "PLAYER",
        "rebounds": "PLAYER",
        "assists": "PLAYER",
        "blocks": "PLAYER",
        "steals": "PLAYER",
        "threes": "PLAYER"
    },
    "MLB": {
        "home_runs": "BATTER",
        "hits": "BATTER",
        "rbis": "BATTER",
        "runs": "BATTER",
        "stolen_bases": "BATTER",
        "pitcher": "PITCHER"
    }
}

def get_sport_key(sport: str) -> str:
    """Get The Odds API sport key for a given sport."""
    return SPORT_KEYS.get(sport, SPORT_KEYS["NFL"])

def get_prop_markets(sport: str) -> List[str]:
    """Get available prop markets for a given sport."""
    return SPORT_PROP_MARKETS.get(sport, SPORT_PROP_MARKETS["NFL"])

def normalize_prop_type(market_key: str, sport: str) -> str:
    """Normalize a market key to standard prop type format."""
    # Remove 'player_' prefix
    prop = market_key.replace("player_", "")

    # Get sport-specific mapping
    mapping = PROP_TYPE_MAPPINGS.get(sport, PROP_TYPE_MAPPINGS["NFL"])

    return mapping.get(prop, prop)

def infer_position(prop_type: str, sport: str) -> str:
    """Infer player position from prop type and sport."""
    inference_map = POSITION_INFERENCE.get(sport, POSITION_INFERENCE["NFL"])

    # Check each keyword in the prop type
    for keyword, position in inference_map.items():
        if keyword in prop_type.lower():
            return position

    return "Unknown"

def get_sport_display_name(sport_key: str) -> str:
    """Convert sport key back to display name."""
    for name, key in SPORT_KEYS.items():
        if key == sport_key:
            return name
    return "NFL"
